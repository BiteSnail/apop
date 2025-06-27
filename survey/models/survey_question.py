from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .question import Question

class SurveyQuestion(models.Model):
    """Question과 Survey의 N:M관계 지원을 위한 모델 클래스
    """    
    survey = models.ForeignKey(
        to="Survey",
        db_comment="survey",
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        to="Question",
        db_comment="question",
        on_delete=models.CASCADE,
    )
    order = models.IntegerField(
        db_column="order",
        db_comment="question order",
        null=False,
        blank=False,
        help_text="질문 순서",
        validators=[MinValueValidator(1)],
    )

    mandatory = models.BooleanField(
        default=False,
        db_column="is_required",
        db_comment="필수 여부",
        help_text="이 질문이 응답해야 하는 필수 항목인지 여부",

    )

    def is_mandatory(self):
        return self.mandatory
    
    def __str__(self) -> str:
        """SurveyQuestion 인스턴스 출력 메서드

        Returns:
            str: Question 제목
        """        
        return self.question.title

    class Meta:
        db_table = "survey_question"
        verbose_name = "설문조사 질문"
        verbose_name_plural = "설문조사 질문"
        ordering = ["survey", "order"]

    @property
    def next_order(self) -> int:
        """가질 수 있는 다음 순서를 반환

        Returns:
            int: 기본적으로 마지막 순서 번호 + 1
        """        
        return SurveyQuestion.objects.filter(survey=self.survey).count() + 1

    def exist_order(self) -> bool:
        """현재 SurveyQuestion의 순서 번호가 이미 존재하는지 확인

        Returns:
            bool: 존재하면 True, 존재하지 않으면 False
        """   
        return SurveyQuestion.objects.filter(survey=self.survey, order=self.order).exists()

    def swap_order(self, order: int):
        """두 SurveyQuestion의 순서 번호를 교환

        Args:
            order (int): 교환하고 싶은 번호
        """        
        if order == self.order:
            return
        survey_question = SurveyQuestion.objects.get(
            survey=self.survey,
            order=order
        )
        survey_question.order, self.order = self.order, survey_question.order
        survey_question.save()
        self.save()
        survey_question.order.save()

    def save(self, *args, **kwargs):
        """순서 번호 자동 설정을 위한 메서드
        """        
        if self.order is None:
            self.order = self.next_order
        if self.exist_order():
            SurveyQuestion.objects.filter(
                survey=self.survey,
                order=self.order
            ).update(
                order=self.next_order
            )

        super().save(*args, **kwargs)