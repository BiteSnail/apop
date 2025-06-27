from django.contrib import admin
from survey.models import SurveyQuestion

# @admin.register(SurveyQuestion)
# class SurveyQuestionAdmin(admin.ModelAdmin):
#     list_display = ('question_text', 'order')
#     list_editable = ('order',)

@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ('survey', 'question', 'order', 'mandatory')
    list_filter = ('survey', 'mandatory')
    search_fields = ('survey__title', 'question__title')
    ordering = ('survey', 'order')


    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'mandatory':
            kwargs['widget'] = admin.widgets.AdminCheckboxWidget
        return super().formfield_for_dbfield(db_field, **kwargs)