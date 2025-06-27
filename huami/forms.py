from django import forms

from .models import HuamiAccount
from .utils import HuamiAmazfit


class HuamiAccountCreationForm(forms.ModelForm):
    """Huami Account생성을 위한 모델 폼
    Raises:
        forms.ValidationError: 이메일이 이미 존재하거나 옳바르지 않은 계정정보인 경우 에러
    """

    class Meta:
        model = HuamiAccount
        fields = (
            'name',
            'email',
            'password',
            'phone_number',
        )
        labels = {
            "name": "이름",
            "email": "Zepp Life 계정 아이디",
            "password": "Zepp Life 계정 비밀번호",
            "phone_number": "핸드폰 번호"

        }

        widgets = {
            'password': forms.PasswordInput(),
            'phone_number': forms.TextInput(attrs={
                'placeholder': '전화번호 입력',
                'pattern': '[0-9-]+',  # 숫자와 하이픈 허용하는 패턴 (대시 없음)
                'maxlength': '11',  # 예시: 최대 11자리 숫자로 제한
                'required': True
            }),

        }

    def __init__(self, *args, **kwargs):
        super(HuamiAccountCreationForm, self).__init__(*args, **kwargs)
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
        self.fields['name'].widget.attrs.update({'class': 'form-control', 'placeholder': '홍길동'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        
    def clean(self) -> dict:
        """폼에 들어온 데이터가 유효한지 검증

        Raises:
            forms.ValidationError: 이메일이 이미 존재하거나 옳바르지 않은 계정정보인 경우 에러

        Returns:
            dict: 검증을 거친 데이터 딕셔너리
        """
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        # email이 Unique한지 확인하는 절차
        self.validate_unique()

        try:
            HuamiAmazfit.is_valid(email, password)
        except ValueError:
            raise forms.ValidationError('이메일이나 비밀번호가 옳바르지 않습니다.')

        return cleaned_data


class HuamiAccountCertificationForm(forms.ModelForm):
    """Huami 재인증을 위한 폼
    Raises:
        forms.ValidationError: 옳바르지 않은 계정정보인 경우 에러
    """

    class Meta:
        model = HuamiAccount
        fields = (
            'name',
            'email',
            'password',
        )

        widgets = {
            'password': forms.PasswordInput()
        }

    def clean(self) -> dict:
        """폼에 들어온 데이터가 유효한지 검증

        Raises:
            forms.ValidationError: 이메일이 이미 존재하거나 옳바르지 않은 계정정보인 경우 에러

        Returns:
            dict: 검증을 거친 데이터 딕셔너리
        """
        cleaned_data = self.cleaned_data
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        try:
            HuamiAmazfit.is_valid(email, password)
        except ValueError:
            raise forms.ValidationError('이메일이나 비밀번호가 옳바르지 않습니다.')

        return cleaned_data
