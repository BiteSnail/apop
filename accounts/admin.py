from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password


# Register your models here.
@admin.action(description='비밀번호 초기화')
def reset_password(modeladmin, request, queryset):
    NEW_PASSWORD = 'password'
    for user in queryset:
        user.password = make_password(NEW_PASSWORD)
        user.save()

    modeladmin.message_user(request, f"선택한 유저의 비밀번호가 '{NEW_PASSWORD}'로 변경되었습니다.")

class CustomUserAdmin(UserAdmin):
    actions = [reset_password]

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), CustomUserAdmin)