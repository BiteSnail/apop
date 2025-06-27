from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response

from accounts.serializers import NormalUserSerializer, UserSerializer
from huami.models.healthdata import HealthData


class IsAdminOrReadOnly(BasePermission):
    """User가 superuser일 때만 list 액션 허용
    """

    def has_permission(self, request, view):
        if view.action == 'update_note':
            return request.user.is_superuser
        if view.action == 'sync_data':
            return request.headers.get('auth-key') == settings.AUTH_KEY
        if view.action in ['list', 'update', 'partial_update']:
            return request.user and request.user.is_superuser


class IsAdminOrOwner(BasePermission):
    """user가 superuser이거나 본인일때만 retrieve 액션 허용
    """

    def has_object_permission(self, request, view, obj):
        return request.user and (request.user.is_superuser or obj == request.user)


def TokenAuthOpenApiParameter():
    return OpenApiParameter(name='Authorization', type=OpenApiTypes.STR, location=OpenApiParameter.HEADER,
                            description="토큰을 입력하세요.", required=True, default="Token your-token")


@extend_schema_view(
    list=extend_schema(
        description="유저 정보들을 제공합니다.",
        parameters=[
            TokenAuthOpenApiParameter()
        ]
    ),
    retrieve=extend_schema(
        description="id와 일치하는 유저의 정보를 제공합니다",
        parameters=[
            TokenAuthOpenApiParameter()
        ]
    ),
    update_note=extend_schema(
        description="id와 일치하는 유저의 비고란을 수정합니다.",
        parameters=[
            TokenAuthOpenApiParameter()
        ],
        request={
            "body": {
                "note": "string"
            }
        }
    )
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """유저 리스트 혹은 개별 유저 데이터 반환
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'retrieve':
            return NormalUserSerializer()
        return super().get_serializer(*args, **kwargs)

    def get_permissions(self):
        if self.action == 'retrieve':
            return [IsAuthenticated(), IsAdminOrOwner()]
        return super().get_permissions()

    def get_queryset(self):
        if self.action == 'list':
            return get_user_model().objects.filter(is_superuser=False)
        return super().get_queryset()

    @action(detail=True, methods=['put'])
    def update_note(self, request, *args, **kwargs):
        if request.data.get('note') is None:
            return Response(data={'message': '형식이 옳바르지 않습니다.'}, status=400)
        user = self.get_object()
        user.huami.note = request.data['note']
        user.huami.save()
        return self.retrieve(request, *args, **kwargs)

    @action(detail=False, methods=["post"])
    def sync_data(self, request, *args, **kwargs):
        sucess_users = []
        failure_users = []

        for user in get_user_model().objects.filter(is_superuser=False):
            try:
                HealthData.create_from_sync_data(user.huami)
                sucess_users.append(user.huami.fullname)
            except Exception as e:
                failure_users.append(user.huami.fullname)
        messages = (len(sucess_users) > 0) * f"{len(sucess_users)}명이 동기화에 성공했습니다."
        messages += (len(failure_users) > 0) * f"{len(failure_users)}명이 동기화에 실패했습니다."

        return JsonResponse({"messages": messages})
