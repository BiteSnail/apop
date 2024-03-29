import csv
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.views import LoginView as Login, LogoutView as Logout
from django.views.generic import View, TemplateView, ListView, DetailView
from django.urls import reverse_lazy
from accounts.utils import make_csv_response
from huami.forms import HuamiAccountCreationForm
from huami.models.healthdata import HealthData
from .forms import MyAuthenticationForm
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from huami.models import HuamiAccount

# Create your views here.
class LoginView(Login):
    """로그인을 위한 클래스 기반 뷰
    """    
    template_name = 'accounts/login.html'
    redirect_field_name = 'redirect_to'
    next_page= reverse_lazy('home')

    
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
        
        #HuamiAccountCreationForm에서 계정 정보가 유효한지 검증
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
    """유저 정보들을 리스트로 제공하기 위한 클래스 기반 뷰
    """    
    template_name = 'accounts/userManage.html'
    model = settings.AUTH_USER_MODEL
    context_object_name = 'users'
    queryset = get_user_model().objects.filter(is_superuser=False)
    paginate_by = 5


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
            health_data = HealthData.create_from_sync_data(user.huami)
            messages.success(request, f"{len(health_data)}일의 데이터가 추가되었습니다.")
        except Exception as e:
            messages.error(request, "동기화 과정 중 오류가 발생하였습니다.")
            
        return redirect(reverse_lazy('accounts:userInfo', kwargs={'pk': pk}))
    

class HealthDataCsvDownloadView(SuperuserRequiredMixin, View):
    """유저 데이터를 csv로 전달하는 클래스 기반 뷰
    get요청만 지원
    """    
    def get(self, request, pk):
        user = get_object_or_404(get_user_model(), pk=pk)
        response = HttpResponse(headers={
            'Content-Type':'text/csv',
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
            'Content-Type':'text/csv',
            'Content-Disposition': f'attachment; filename="{pk}.csv"'})

        return make_csv_response(user, response)
    
class UserPrimaryKeyAPIView(AuthKeyRequiredMixin, View):
    """일반유저들의 이름과 대응하는 PK를 전달하는 API 클래스 기반 뷰
    get 요청만 지원
    """    
    def get(self, request: HttpRequest):
        response = HttpResponse(headers={
            'Content-Type':'text/csv',
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
                line.append(user.huami.full_name)
            line.append(user.pk)
            file.writerow(line)
        
        return response
    