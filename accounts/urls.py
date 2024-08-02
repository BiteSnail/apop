from django.urls import path
from .views import HealthDataCsvDownloadAPIView, HealthDataCsvDownloadView, LoginView, LogoutView, SignUpView, SuccessSignUpView, UserHealthDataSyncView, UserHealthNoteUpdateView, UserInfoView, UserManageView, UserNoteUpdateView, UserPrimaryKeyAPIView, password_reset_request, verify_code, password_reset_confirm, password_reset_complete, find_username_request, verify_username_code
from django.contrib.auth import views as auth_views
app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('successSignup/', SuccessSignUpView.as_view(), name='successSignup'),
    path('manage/', UserManageView.as_view(), name='userManage'),
    path('info/<int:pk>/', UserInfoView.as_view(), name='userInfo'),
    path('heatlhInfo/<int:pk>/', UserHealthNoteUpdateView.as_view(), name='userHealthInfo'),
    path('<int:pk>/updateNote/', UserNoteUpdateView.as_view(), name='updateNote'),
    path('<int:pk>/syncData/', UserHealthDataSyncView.as_view(), name='syncHealth'),
    path('<int:pk>/csvData/', HealthDataCsvDownloadView.as_view(), name='csvDownload'),
    path('users/<int:pk>/healthData.csv', HealthDataCsvDownloadAPIView.as_view(), name='csvDownloadApi'),
    path('users.csv', UserPrimaryKeyAPIView.as_view(), name="usersCsvDownloadApi"),

    path('password_reset/', password_reset_request, name='password_reset_request'),
    path('verify_code/', verify_code, name='verify_code'),
    path('reset/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', password_reset_complete, name='password_reset_complete'),
    path('find_username/', find_username_request, name='find_username_request'),
    path('verify_username_code/<str:email>/', verify_username_code, name='verify_username_code')


]
