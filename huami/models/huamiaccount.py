from datetime import datetime

from django.conf import settings
from django.db import models
from requests import HTTPError

from huami.utils import HuamiAmazfit

default_sny_date = datetime(1970, 1, 1)


class HuamiAccount(models.Model):
    """HuamiAccount 모델 클래스
    """
    RESEARCH_STATUS_CHOICES = [
        ('ongoing', '진행 중'),
        ('completed', '종료'),
        ('preparing', '준비'),
    ]

    RESEARCH_YEAR_CHOICES = [
        ('none', '미확인'),
        ('2023', '2023'),
        ('2024', '2024'),
    ]
    user = models.OneToOneField(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        db_comment="user id",
        null=False,
        blank=False,
        help_text="유저 id",
        related_name="huami",
    )
    email = models.EmailField(
        db_column="email",
        db_comment="huami account email address",
        null=False,
        blank=False,
        unique=True,
        help_text="화웨이(Zepp Life) 계정 이메일"
    )
    password = models.CharField(
        db_column="password",
        db_comment="huami account password address",
        max_length=100,
        null=False,
        blank=False,
        help_text="화웨이(Zepp Life) 계정 패스워드"
    )
    research_status = models.CharField(
        db_column="research_status",
        max_length=10,
        choices=RESEARCH_STATUS_CHOICES,
        default='preparing',  # 기본값 설정
    )
    join_date = models.DateTimeField(
        db_column="join_date",
        null=True,
        help_text="연구 시작일"
    )
    end_date = models.DateTimeField(
        db_column="end_date",
        null=True,
        help_text="연구 종료일"
    )
    showed_sync_status = models.BooleanField(
        db_column="showed_sync_status",
        null=False,
        default=True,
        help_text="동기화 가능 여부"
    )
    name = models.CharField(
        db_column="name",
        max_length=100,
        null=True,
        help_text="사용자 이름"
    )
    sync_date = models.DateTimeField(
        db_column="sync_date",
        db_comment="huami account sync date",
        null=False,
        blank=False,
        help_text="화웨이(Zepp Life) 계정 동기화 날짜",
        default=default_sny_date,
    )
    note = models.TextField(
        db_column="note",
        db_comment="information of user",
        null=True,
        blank=True,
        help_text="사용자에 대한 간략한 설명",
        default="정보를 입력해주세요."
    )
    age = models.IntegerField(
        db_column="age",
        null=True,
        help_text="사용자의 나이"
    )

    phone_number = models.CharField(
        db_column="phone_number",
        max_length=15,  # 전화번호 길이에 맞게 조정 가능, 010-1234-5678 형식으로 저장
        null=True,
        help_text="전화번호를 입력해 주세요"
    )


    pregnancy_start_date = models.DateTimeField( #yyyy-mm-dd 형식의 string으로 저장
        db_column="pregnancy_start_date",
        db_comment="임신 시작일",
        null=True,
        blank=True,
        help_text="임신 시작일을 입력해주세요"
    )

    research_year = models.CharField(
        db_column="research_year",
        max_length=6,
        choices=RESEARCH_YEAR_CHOICES,
        default='none',  # 기본값 설정
    )




    @property
    def fullname(self) -> str:
        return f"{self.user.last_name} {self.user.first_name}"

    @property
    def last_health_info(self):
        return self.health.last()

    @property
    def sync_status(self) -> str:
        try:
            HuamiAmazfit.is_valid(self.email, self.password)
        except Exception as e:
            return "데이터 동기화가 중단되었습니다! 화웨이 계정 재설정을 진행해 주세요!"
        return "정상"

    def __str__(self) -> str:
        """HuamiAccount 인스턴스 출력 메서드

        Returns:
            str: Huami 계정 이메일
        """
        return self.email

    class Meta:
        db_table = "huami_account"
        verbose_name = "화웨이 계정"
        verbose_name_plural = "화웨이 계정"
        ordering = ["email", "sync_date"]

    def reset_sync_date(self) -> None:
        """동기화 시간 초기화
        """
        self.sync_date = default_sny_date
        self.save()

    def get_data(self) -> dict:
        """현재 계정 정보로 데이터 수집

        Raises:
            HTTPError: 처리 과정 중 오류

        Returns:
            dict: 심박수, 스트레스, 걸음 수, 수면 질, SPO2, 무게, 키 에 대한 정보
        """
        result = {}
        account = HuamiAmazfit(email=self.email, password=self.password)
        try:
            account.access()
            account.login()
            result['profile'] = account.profile()
            result['band'] = account.band_data('2023-01-01', datetime.now().strftime('%Y-%m-%d'))
            result['stress'] = account.stress('2023-01-01', datetime.now().strftime('%Y-%m-%d'))
            result['blood'] = account.blood_oxygen('2023-01-01', datetime.now().strftime('%Y-%m-%d'))
            account.logout()
        except HTTPError as e:
            raise HTTPError("데이터를 받아오는 과정에서 오류가 발생하였습니다. 오류내용: " + e)
        self.sync_date = datetime.now()
        self.save()

        return result

# Create your models here.




