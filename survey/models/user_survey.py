from django.db import models
from django.conf import settings


class UserSurvey(models.Model):
    """UserSurvey 모델 클래스
    User가 같은 survey라도 여러 번 수행할 수 있으므로
    UserSurvey 테이블로 하나의 설문지 작성을 표현
    """    
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column='user_id',
        db_comment='user id',
        null=False,
        blank=False,
        help_text='유저 id',
        related_name="user_survey"
    )
    survey = models.ForeignKey(
        to='Survey',
        on_delete=models.CASCADE,
        db_column='survey_id',
        db_comment='survey id',
        null=False,
        blank=False,
        help_text='설문 id'
    )
    create_at = models.DateTimeField(
        db_column='create_at',
        db_comment='user survey created time',
        auto_now_add=True,
        help_text='유저 설문 생성 시간'
    )
    updated_at = models.DateTimeField(
        db_column='updated_at',
        db_comment='user survey updated time',
        auto_now=True,
        help_text='유저 설문 수정 시간'
    )
    
    @property
    def survey_name(self) -> str:
        return self.survey.title
    
    @property
    def counts(self) -> int:
        return UserSurvey.objects.filter(user=self.user, survey=self.survey).count()

    class Meta:
        db_table = 'user_survey'
        verbose_name = '유저 설문'
        verbose_name_plural = '유저 설문'
        ordering = ['create_at']

    def replies(self) -> models.QuerySet:
        """설문지 인스턴스에 대한 응답들 반환

        Returns:
            models.QuerySet: 응답들
        """        
        return self.replies().all()
