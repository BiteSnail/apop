from django.db import models


class Answer(models.Model):
    """Answer 모델 클래스
    Question에 대한 가능한 답변
    """    
    description = models.CharField(
        db_column='description',
        db_comment='description of answer',
        max_length=100,
        null=False,
        blank=False,
        help_text='질문 답변의 내용입니다.'
    )
    create_at = models.DateTimeField(
        db_column='create_at',
        db_comment='answer created time',
        auto_now_add=True,
        help_text='질문 답변의 생성 시간입니다.'
    )
    updated_at = models.DateTimeField(
        db_column='updated_at',
        db_comment='answer updated time',
        auto_now=True,
        help_text='질문 답변의 수정 시간입니다.'
    )
    value = models.IntegerField(
        db_column='value',
        null=True,
        blank=True,
        help_text='질문에 값이 존재할 경우 값을 기재합니다.'
    )
    is_other = models.BooleanField(
        db_column="is_other",
        db_comment="기타 옵션 여부",
        default=False,
        help_text="이 응답이 기타 옵션인지 여부"
    )


    class Meta:
        db_table = 'answer'
        verbose_name = '답변'
        verbose_name_plural = '답변'
        ordering = ['create_at']

    def __str__(self) -> str:
        """Answer 인스턴스 출력 메서드

        Returns:
            str: 답변의 내용
        """        
        return self.description