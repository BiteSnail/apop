import csv
import hashlib
import json
import base64
import urllib.parse


import requests.exceptions
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView as Login, LogoutView as Logout, PasswordChangeView
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import View, TemplateView, ListView, DetailView

from accounts.utils import make_csv_response
from huami.forms import HuamiAccountCreationForm, HuamiAccountCertificationForm
from huami.models import HuamiAccount
from huami.models.healthdata import HealthData
from .forms import MyAuthenticationForm, MyLoginForm, PhoneNumberChangeForm
from .forms import EmailPasswordResetRequestForm, VerifyCodeForm, SetPasswordForm, FindUsernameForm,PhoneNumberPasswordResetRequestForm
from .models import Profile
from .utils import generate_verification_code
from fitbit.models import FitbitAccount
from django.contrib.auth import login
from django.utils.timezone import now, timedelta
from django.utils.crypto import get_random_string
from django.utils.timezone import now, timedelta
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse
import requests
import base64
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.models import User


# Create your views here.
class LoginView(Login):
    """로그인을 위한 클래스 기반 뷰
    """
    template_name = 'accounts/admin_login.html'
    redirect_field_name = 'redirect_to'
    next_page = reverse_lazy('home')
    form_class = MyLoginForm


class LogoutView(Logout):
    """로그아웃을 위한 클래스 기반 뷰
    """
    template_name = 'accounts/login.html'
    redirect_field_name = 'redirect_to'
    next_page = reverse_lazy('home')


class SignUpView(View):
    """회원가입 페이지를 제공하는 클래스 기반 뷰
    """
    form_class = [HuamiAccountCreationForm, MyAuthenticationForm]
    template_name = 'accounts/signup.html'

    def get(self, request, *args, **kwargs):
        """회원가입 폼 입력 화면

        Args:
            request (HttpRequest): HttpRequest 정보

        Returns:
            HttpResponse: 렌더링 된 입력화면 HTML
        """
        account_form = self.form_class[1]
        huami_account_form = self.form_class[0]
        return render(request, self.template_name, {'account_form': account_form,
                                                    'huami_account_form': huami_account_form})

    def post(self, request, *args, **kwargs):
        """회원가입 폼 제출 화면

        Args:
            request (HttpRequest): HttpRequest 정보

        Returns:
            HttpResponse: 입력에 따라 렌러딩 된 결과화면 HTML
        """
        account_form = self.form_class[1](request.POST)
        huami_account_form = self.form_class[0](request.POST)

        # HuamiAccountCreationForm에서 계정 정보가 유효한지 검증
        if account_form.is_valid() and huami_account_form.is_valid():
            user = account_form.save()
            huami_account = huami_account_form.save(commit=False)
            huami_account.user = user
            huami_account.save()

            return redirect('accounts:successSignup')

        return render(request, self.template_name, {'account_form': account_form,
                                                    'huami_account_form': huami_account_form})


class SuccessSignUpView(TemplateView):
    """회원가입 성공 화면 제공을 위한 클래스 기반 뷰
    """
    template_name = 'accounts/successSignup.html'


class SuperuserRequiredMixin(UserPassesTestMixin):
    """관리자만 접근하도록 지정하는 믹스인
    """

    def test_func(self):
        return self.request.user.is_superuser


class UserInfoView(SuperuserRequiredMixin, DetailView):
    """유저 정보를 제공하기 위한 클래스 기반 뷰
    """
    model = get_user_model()
    context_object_name = 'userInfo'
    template_name = 'accounts/userInfo.html'


class UserManageView(SuperuserRequiredMixin, ListView):
    """HuamiAccount가 연결된 유저들만 리스트로 제공"""
    template_name = 'accounts/userManage.html'
    model = get_user_model()  # settings.AUTH_USER_MODEL보다 명시적
    context_object_name = 'users'
    queryset = get_user_model().objects.filter(is_superuser=False,huami__isnull=False).select_related('huami')
    paginate_by = 10

    def get_queryset(self):
        query_set = get_user_model().objects.filter(
            is_superuser=False,
            huami__isnull=False
        ).select_related('huami', 'fitbit')

        query_set = super().get_queryset().select_related('huami', 'fitbit')

        search_query = self.request.GET.get('search', '')
        if search_query:
            from django.db.models import Q
            query_set = query_set.filter(
                Q(huami__name__icontains=search_query) |
                Q(huami__email__icontains=search_query)
            )

        order_by = self.request.GET.get('order_by', 'huami__name')
        direction = self.request.GET.get('direction', 'asc')
        if direction == 'desc':
            order_by = f'-{order_by}'

        return query_set.order_by(order_by)



class UserNoteUpdateView(SuperuserRequiredMixin, View):
    """유저에 대한 비고란을 수정하기 위한 클래스 기반 뷰
    post요청만 지원
    """

    def post(self, request, pk):
        user = get_object_or_404(get_user_model(), pk=pk)
        user.huami.note = request.POST['note']
        user.huami.save()
        return redirect(reverse_lazy('accounts:userInfo', kwargs={'pk': pk}))


class UserHealthNoteUpdateView(SuperuserRequiredMixin, View):
    """유저가 가진 건강 정보의 비고란을 수정하기 위한 클래스 기반 뷰
    post요청만 지원
    """

    def post(self, request, pk):
        health_data = get_object_or_404(HealthData, pk=pk)
        health_data.note = request.POST['note']
        health_data.save()
        return redirect(reverse_lazy('accounts:userInfo', kwargs={'pk': health_data.huami_account.user.pk}))


class UserHealthDataSyncView(SuperuserRequiredMixin, View):
    """유저의 데이터 동기화를 위한 클래스 기반 뷰
    get요청만 지원
    """

    def get(self, request, pk):
        user = get_object_or_404(get_user_model(), pk=pk)
        try:
            age, health_data = HealthData.create_from_sync_data(user.huami)
            user.huami.age = age
            user.huami.save()
            messages.success(request, f"{len(health_data)}일의 데이터가 추가되었습니다.")
        except requests.HTTPError as e:
            messages.error(request, "동기화 과정 중 오류가 발생하였습니다." + str(e.response.reason))

        except Exception as e:
            messages.error(request, "동기화 과정 중 오류가 발생하였습니다." + str(e))

        return redirect(reverse_lazy('accounts:userInfo', kwargs={'pk': pk}))


class HealthDataCsvDownloadView(SuperuserRequiredMixin, View):
    """유저 데이터를 csv로 전달하는 클래스 기반 뷰
    get요청만 지원
    """

    def get(self, request, pk):
        user = get_object_or_404(get_user_model(), pk=pk)
        response = HttpResponse(headers={
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename="{pk}.csv"'})

        return make_csv_response(user, response)


class AuthKeyRequiredMixin(UserPassesTestMixin):
    """headers에 auth-key가 존재하는지 여부 확인
    """

    def test_func(self):
        return self.request.headers.get('auth-key') == settings.AUTH_KEY

    def handle_no_permission(self):
        return HttpResponse("You have not permission")


class HealthDataCsvDownloadAPIView(AuthKeyRequiredMixin, View):
    """데이터를 가져올 유저의 pk를 리스트로 받아서 해당하는 유저들의 데이터를 csv파일로 전달하는 API 클래스 기반 뷰
    get 요청만 지원
    """

    def get(self, request: HttpRequest, pk: int):
        if get_user_model().objects.filter(pk=pk).exists() == False:
            return HttpResponse("No person in users")

        user = get_object_or_404(get_user_model(), pk=pk)

        if HuamiAccount.objects.filter(user=user).exists() == False:
            return HttpResponse("No huami account in user")

        response = HttpResponse(headers={
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename="{pk}.csv"'})

        return make_csv_response(user, response)


class UserPrimaryKeyAPIView(AuthKeyRequiredMixin, View):
    """일반유저들의 이름과 대응하는 PK를 전달하는 API 클래스 기반 뷰
    get 요청만 지원
    """

    def get(self, request: HttpRequest):
        response = HttpResponse(headers={
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename="users.csv"'})

        file = csv.writer(response)
        head_line = []
        if request.headers.get('fullname') == 'True':
            head_line.append('fullname')
        head_line.append('pk')
        file.writerow(head_line)

        for user in get_user_model().objects.filter(is_superuser=False).all():
            line = []
            if request.headers.get('fullname') == 'True':
                line.append(user.huami.fullname)
            line.append(user.pk)
            file.writerow(line)

        return response


class UserProfileView(LoginRequiredMixin, View):
    template_name = "accounts/myprofile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = self.request.user
        context['email_hash'] = hashlib.md5(self.request.user.huami.email.encode('utf-8').strip().lower()).hexdigest()
        return context

    def get(self, request):
        return render(request, self.template_name, {'current_user': request.user})


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/change_password.html"
    form_class = PasswordChangeForm
    success_url = reverse_lazy('accounts:user_profile')


class UserPhoneNumberChangeView(LoginRequiredMixin, View):
    # 전화전호 수정 뷰 로직
    template_name = "accounts/change_phone_number.html"
    form_class = PhoneNumberChangeForm

    def get(self, request):
        form = PhoneNumberChangeForm
        return render(request, self.template_name, {'current_user': request.user, 'form': form})

    success_url = reverse_lazy('accounts:user_profile')

    def post(self, request, *args, **kwargs):
        form = PhoneNumberChangeForm(request.POST)
        if form.is_valid():
            huami_account = HuamiAccount.objects.get(user=request.user)
            huami_account.phone_number = form.cleaned_data['phone_number']
            huami_account.save()

            return redirect(reverse_lazy('accounts:user_profile'))
        return render(request, self.template_name, {'current_user': request.user, 'form': form})


class HuamiAccountRecertificationView(LoginRequiredMixin, SignUpView):
    template_name = "accounts/recertification.html"
    form_class = HuamiAccountCertificationForm
    success_url = reverse_lazy('accounts:user_profile')

    def get(self, request, *args, **kwargs):
        form = HuamiAccountCertificationForm
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = HuamiAccountCertificationForm(request.POST)
        if form.is_valid():
            huami_account = HuamiAccount.objects.get(user=request.user)
            huami_account.email = form.cleaned_data['email']
            huami_account.password = form.cleaned_data['password']
            huami_account.save()

            return redirect(reverse_lazy('accounts:user_profile'))

        return render(request, self.template_name, {'form': form})


def create_profile_if_not_exists(user):
    """profile 생성
     """
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        Profile.objects.create(user=user)

def select_password_reset_request(request):
    return render(request, "accounts/select_reset_password.html")


def email_password_reset_request(request):
    """비밀번호 찾기 시 정보 저장
     """
    if request.method == 'POST':
        form = EmailPasswordResetRequestForm(request.POST)
        if form.is_valid():

            username = form.cleaned_data['username']
            email = form.cleaned_data['email']

            try:
                huami_account = HuamiAccount.objects.get(email=email)
                user = User.objects.get(username=username)
                create_profile_if_not_exists(user)
                verification_code = generate_verification_code()
                user.profile.verification_code = verification_code
                user.profile.save()

                request.session['reset_username'] = username

                send_mail(
                    'Password Reset Verification Code',
                    f'Your verification code is {verification_code}',
                    'pregnancy_re@naver.com',
                    [huami_account.email],
                    fail_silently=False,
                )

                messages.success(request, 'Verification code sent to your email.')
                return redirect('accounts:verify_code')
            except HuamiAccount.DoesNotExist:
                messages.error(request, '등록되지 않은 이메일입니다.')
            except User.DoesNotExist:
                messages.error(request, '아이디가 존재하지 않습니다.')
    else:
        form = EmailPasswordResetRequestForm()
    return render(request, "accounts/email_password_reset_request.html", {"form": form})

def phone_number_password_reset_request(request):
    """비밀번호 찾기 시 정보 저장
     """
    if request.method == 'POST':
        form = PhoneNumberPasswordResetRequestForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            phone_number = form.cleaned_data['phone_number']
            """유저의 핸드폰, 이름 아이디 확인"""
            try:
                user = User.objects.get(username=username)
                create_profile_if_not_exists(user)
                huami_account = HuamiAccount.objects.get(user=user)
                if phone_number == huami_account.phone_number :
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    return redirect('accounts:password_reset_confirm', uidb64=uid, token=token)
                else:
                    messages.error(request, '전화번호가 일치하지 않습니다.')
            except User.DoesNotExist:
                messages.error(request, '아이디가 존재하지 않습니다.')
    else:
        form = PhoneNumberPasswordResetRequestForm()
    return render(request, "accounts/phone_number_password_reset_request.html", {"form": form})


def verify_code(request):
    """비밀번호 변경 시 인증코드 확인하는 코드
     """
    if request.method == 'POST':
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            username = request.session.get('reset_username')
            verification_code = form.cleaned_data['verification_code']

            if not username:
                messages.error(request, 'No username found in session. Please start over.')
                return redirect('accounts:email_password_reset_request')

            try:
                user = User.objects.get(username=username)
                create_profile_if_not_exists(user)

                if user.profile.verification_code == verification_code:
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    return redirect('accounts:password_reset_confirm', uidb64=uid, token=token)
                else:
                    messages.error(request, 'Invalid verification code.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = VerifyCodeForm()
    return render(request, 'accounts/verify_code.html', {'form': form})


def password_reset_confirm(request, uidb64=None, token=None):
    """새로운 비밀번호 변경 관련 코드
     """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password was successfully updated!')
                return redirect('accounts:password_reset_complete')
        else:
            form = SetPasswordForm(user)
    else:
        messages.error(request, "The reset link is no longer valid.")
        return redirect("accounts:email_password_reset_request")

    return render(request, 'accounts/password_reset_confirm.html', {'form': form})


def password_reset_complete(request):
    return render(request, 'accounts/password_reset_complete.html')


def find_username_request(request):
    """ID찾기 시 정보 저장
     """
    if request.method == 'POST':
        form = FindUsernameForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']

            try:
                user = HuamiAccount.objects.get(email=email, name=name).user

                create_profile_if_not_exists(user)

                verification_code = generate_verification_code()
                user.profile.verification_code = verification_code
                user.profile.save()

                request.session['reset_email'] = email

                send_mail(
                    '진통감지 및 스트레스 완화연구 사이트 인증코드',
                    f'인증코드는 다음과 같습니다.: {verification_code}',
                    'pregnancy_re@naver.com',
                    [email],
                    fail_silently=False,
                )

                messages.success(request, '이메일로 인증번호를 발송하였습니다')
                return redirect('accounts:verify_username_code', email=email)
            except HuamiAccount.DoesNotExist:
                messages.error(request, '이메일과 이름이 일치하지 않습니다!')
    else:
        form = FindUsernameForm()
    return render(request, 'accounts/find_username_request.html', {'form': form})


def verify_username_code(request, email):
    """ID 찾기 시 인증코드 확인 코드
     """
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code')
        email = request.session.get('reset_email')

        if not email:
            messages.error(request, 'No email found in session. Please start over.')
            return redirect('accounts:find_username_request')

        try:
            huami_account = HuamiAccount.objects.get(email=email)
            user = User.objects.get(id=huami_account.user_id)

            if user.profile.verification_code == verification_code:
                return render(request, 'accounts/username_complete.html', {'username': user.username})
            else:
                messages.error(request, 'Invalid verification code.')

        except HuamiAccount.DoesNotExist:
            messages.error(request, 'Email not found in HuamiAccount.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return render(request, 'accounts/verify_username_code.html', {'email': email})


class UserResearchStatus(SuperuserRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)

        user_id = data.get('user_id')
        new_status = data.get('new_status')

        try:
            user = User.objects.get(pk=user_id)
            user.huami.research_status = new_status
            user.huami.save()

            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})

class UserResearchYear(SuperuserRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)

        user_id = data.get('user_id')
        new_year = data.get('new_year')

        try:
            user = User.objects.get(pk=user_id)
            user.huami.research_year = new_year
            user.huami.save()

            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})


class UserResearchDate(SuperuserRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)

        user_id = data.get('user_id')
        new_date = data.get('new_date')
        date_type = data.get('date_type')

        try:
            user = User.objects.get(pk=user_id)
            if date_type == 'join-date':
                user.huami.join_date = new_date
            elif date_type == 'end-date':
                user.huami.end_date = new_date
            elif date_type == 'pregnancy_start_date':
                user.huami.pregnancy_start_date=new_date
            user.huami.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})


class FitbitLoginView(View):
    def get(self, request):
        client_id = "23QDQ6"
        redirect_uri = "https://dai427.cbnu.ac.kr/accounts/callback/"
        scope = [
            "activity", "heartrate", "sleep", "nutrition", "weight",
            "profile", "location", "oxygen_saturation", "respiratory_rate", "temperature"
        ]

        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scope)
        }

        auth_url = "https://www.fitbit.com/oauth2/authorize?" + urllib.parse.urlencode(params)
        return redirect(auth_url)


import base64
import requests
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views import View




class FitbitCallbackView(View):
    def get(self, request):
        code = request.GET.get("code")
        if not code:
            return JsonResponse({"error": "Authorization code not found"}, status=400)


        redirect_uri = "https://dai427.cbnu.ac.kr/accounts/callback/"
        token_url = "https://api.fitbit.com/oauth2/token"

        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "client_id": client_id,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code
        }

        token_response = requests.post(token_url, headers=headers, data=data)
        if token_response.status_code != 200:
            return JsonResponse({"error": "Failed to retrieve token", "details": token_response.json()}, status=token_response.status_code)

        token_data = token_response.json()
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data["expires_in"]
        scope = token_data["scope"]
        token_type = token_data["token_type"]

        profile_response = requests.get(
            "https://api.fitbit.com/1/user/-/profile.json",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if profile_response.status_code != 200:
            return JsonResponse({"error": "Failed to fetch profile"}, status=profile_response.status_code)

        profile_data = profile_response.json().get("user", {})
        fitbit_user_id = profile_data["encodedId"]
        full_name = profile_data.get("fullName")
        gender = profile_data.get("gender")
        birthday = profile_data.get("dateOfBirth")
        height = profile_data.get("height")
        weight = profile_data.get("weight")

        # 유저 생성 또는 가져오기
        user, created = User.objects.get_or_create(
            username=f"fitbit_{fitbit_user_id}",
            defaults={"first_name": full_name or ""}
        )

        if created:
            user.set_password(get_random_string(length=12))
            user.save()

        FitbitAccount.objects.update_or_create(
            user=user,
            defaults={
                "fitbit_user_id": fitbit_user_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": now() + timedelta(seconds=expires_in),
                "scope": scope,
                "token_type": token_type,
                "full_name": full_name,
                "gender": gender,
                "birthday": birthday,
                "height": height,
                "weight": weight,
                "last_synced": now()
            }
        )

        login(request, user)
        print("Fitbit OAuth 성공 - 홈으로 리디렉트 시도")
        return redirect(reverse("home"))

#로그인 방식 선택
def login_select(request):
    return render(request, 'accounts/login.html')