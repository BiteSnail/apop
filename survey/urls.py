from django.urls import path
from django.views.generic import TemplateView
from survey.views import SurveyListView, SurveyDetailView, SurveyFormView, UserSurveyListView, SurveyListAdminView, \
    UserSurveyListAdminView, UserSurveyCsvView

app_name = 'survey'

urlpatterns = [
    path('<int:pk>', SurveyFormView.as_view(), name='survey-detail'),
    path('<int:pk>/user/', UserSurveyListView.as_view(), name='user-survey-list'),
    path('', SurveyListView.as_view(), name='survey-list'),
    path('user/<int:pk>/', SurveyListAdminView.as_view(), name='survey-list-admin'),
    path('<int:survey_pk>/user/<int:user_pk>/', UserSurveyListAdminView.as_view(), name='user-survey-list-admin'),
    path('<int:survey_pk>/user/<int:user_pk>/csv/', UserSurveyCsvView.as_view(), name='user-survey-csv'),
]