from django.contrib import admin

from survey.models import Answer


class AnswerAdmin(admin.ModelAdmin):
    """Answer 모델 어드민
    """    
    fields = ['description', 'value', 'is_other']
    list_display = ['description', 'value', 'is_other']
    list_display_links = ['description']
    search_fields = ['description']
    search_help_text = "설명을 입력하세요"
    list_filter = ['is_other']


admin.site.register(Answer, AnswerAdmin)