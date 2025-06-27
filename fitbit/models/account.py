from django.db import models
from django.conf import settings


class FitbitAccount(models.Model):
    user = models.OneToOneField(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fitbit',
        help_text="이 계정과 연결된 유저"
    )

    fitbit_user_id = models.CharField(
        max_length=128,
        unique=True,
        help_text="Fitbit에서 받은 고유 사용자 ID"
    )

    access_token = models.TextField(
        help_text="Fitbit API 접근용 액세스 토큰"
    )

    refresh_token = models.TextField(
        help_text="액세스 토큰 갱신용 리프레시 토큰"
    )

    expires_at = models.DateTimeField(
        help_text="액세스 토큰 만료 시간"
    )

    scope = models.TextField(
        help_text="발급받은 권한 범위"
    )

    token_type = models.CharField(
        max_length=20,
        default='Bearer',
        help_text="토큰 타입 (보통 Bearer)"
    )

    full_name = models.CharField(
        max_length=100,
        null=True,
        help_text="Fitbit 프로필에서 가져온 이름"
    )

    gender = models.CharField(
        max_length=10,
        null=True,
        help_text="성별 (male/female/NA 등)"
    )

    birthday = models.DateField(
        null=True,
        help_text="생년월일"
    )

    height = models.FloatField(
        null=True,
        help_text="신장 (cm 또는 m 단위, Fitbit API 단위에 따라 조정)"
    )

    weight = models.FloatField(
        null=True,
        help_text="몸무게 (kg)"
    )

    last_synced = models.DateTimeField(
        null=True,
        help_text="마지막 데이터 동기화 시간"
    )

    def __str__(self):
        return f"{self.user.username} - FitbitAccount"

    class Meta:
        verbose_name = "핏빗 계정"
        verbose_name_plural = "핏빗 계정"
