from django.urls import path, include
from rest_framework.authtoken import views
from accounts.apiviews import UserViewSet
from rest_framework import routers
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('token/', views.obtain_auth_token),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('', include(router.urls))
]