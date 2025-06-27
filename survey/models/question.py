from collections import namedtuple

from django.db import models

TYPE_FILED = namedtuple(
    "TYPE_FIELD", "text number radio select multi_select text_area"
)._make(range(6))


class Question(models.Model):
    """Question 모델 클래스
    Survey에서 수행해야 하는 질문
    """    
    TYPE_FILED = [
        (TYPE_FILED.text, "text"),
        (TYPE_FILED.number, "number"),
        (TYPE_FILED.radio, "radio"),
        (TYPE_FILED.select, "select"),
        (TYPE_FILED.multi_select, "multi_select"),
        (TYPE_FILED.text_area, "text_area"),
    ]
    title = models.CharField(
        db_column="title",
        db_comment="question title",
        null=False,
        blank=False,
        help_text="질문 제목",
        max_length=70
    )
    description = models.TextField(
        db_column="description",
        db_comment="question description",
        null=True,
        blank=False,
        help_text="질문 설명",
        max_length=100
    )
    create_at = models.DateTimeField(
        db_column="create_at",
        db_comment="question created time",
        auto_now_add=True,
        help_text="질문 생성 시간"
    )
    updated_at = models.DateTimeField(
        db_column="updated_at",
        db_comment="question updated time",
        auto_now=True,
        help_text="질문 수정 시간"
    )
    answers = models.ManyToManyField(
        to="Answer",
        through="QuestionAnswer",
        related_name="questions",
    )
    type_filed = models.PositiveSmallIntegerField(
        db_column="type_filed",
        db_comment="question type",
        null=False,
        choices=TYPE_FILED,
        help_text="질문 타입",
        default=2
    )

    class Meta:
        db_table = "question"
        verbose_name = "질문"
        verbose_name_plural = "질문"
        ordering = ["create_at"]

    def __str__(self) -> str:
        """Question 인스턴스 출력 메서드

        Returns:
            str: Question 제목
        """        
        return self.title