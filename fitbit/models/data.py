# fitbit/data.py
"""
Fitbit minute-level 통합 데이터 모델 (패턴 A: 한 행에 여러 센서값을 부분 갱신)

‣ (account, timestamp) 조합이 유일하도록 UNIQUE 제약을 둠
‣ 모든 항목은 NULL 허용 → 값이 들어올 때만 채워진다.
"""

from django.db import models
from django.utils import timezone

from .account import FitbitAccount   # 같은 패키지 내 account.py 의 모델


class FitbitMinuteMetric(models.Model):
    """
    ✔ account + timestamp(분) UNIQUE
    ✔ 분단위로 여러 센서 값을 ‘빈 칸 메우기(upsert)’ 방식으로 저장
    """

    # ------------- 공통 키 -------------
    account = models.ForeignKey(
        FitbitAccount,
        on_delete=models.CASCADE,
        related_name="minute_metrics",
        help_text="연결된 Fitbit 계정"
    )
    timestamp = models.DateTimeField(
        help_text="데이터 기준 시각(UTC, 1 분 그리드 권장)"
    )

    # 1) 심박수 (bpm)
    heart_rate = models.PositiveSmallIntegerField(
        null=True,
        help_text="심박수 (bpm)"
    )

    # 2) 활동량 (걸음 수·스텝)
    step_count = models.PositiveIntegerField(
        null=True,
        help_text="1분 동안의 걸음 수"
    )

    # 3) 수면 단계 / 질
    SLEEP_STAGE_CHOICES = [
        ("wake",  "깸"),
        ("light", "얕은잠"),
        ("deep",  "깊은잠"),
        ("rem",   "REM"),
    ]
    sleep_stage = models.CharField(
        max_length=5,
        choices=SLEEP_STAGE_CHOICES,
        null=True,
        help_text="수면 단계(wake/light/deep/rem)"
    )

    # 4) SpO₂ (%)
    spo2 = models.FloatField(
        null=True,
        help_text="혈중 산소포화도 (%)"
    )

    # 5) 호흡수 (breaths/min)
    respiratory_rate = models.FloatField(
        null=True,
        help_text="호흡수 (breaths per minute)"
    )

    # 6) 피부 온도 (°C)
    skin_temperature = models.FloatField(
        null=True,
        help_text="피부 온도 (°C)"
    )

    # 7) 몸무게 (kg)
    weight_kg = models.FloatField(
        null=True,
        help_text="몸무게 (kg)"
    )

    # 8) 키 (cm)
    height_cm = models.FloatField(
        null=True,
        help_text="키 (cm)"
    )

    # 9) 나이 (years)
    age_years = models.PositiveSmallIntegerField(
        null=True,
        help_text="나이 (세)"
    )

    # ------------- 메타정보 -------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------- Python 표현 -------------
    def __str__(self) -> str:
        local_ts = timezone.localtime(self.timestamp)
        return f"{self.account.user.username} @ {local_ts:%Y-%m-%d %H:%M}"

    class Meta:
        verbose_name = "분 단위 통합 메트릭"
        verbose_name_plural = "분 단위 통합 메트릭"
        # account + timestamp 조합에 유일성 부여 (분 단위 UNIQUE 키)
        constraints = [
            models.UniqueConstraint(
                fields=["account", "timestamp"],
                name="unique_minute_per_account"
            )
        ]
        # 조회 성능용 인덱스 (계정별 시간역순 조회가 가장 흔함)
        indexes = [
            models.Index(fields=["account", "-timestamp"]),
        ]
