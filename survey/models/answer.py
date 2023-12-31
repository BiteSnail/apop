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