from django.contrib import admin

# Register your models here.
from huami.models import HuamiAccount, HealthData


class HuamiAccountAdmin(admin.ModelAdmin):
    """HuamiAccount 모델 어드민
    """
    fields = ['user', 'email', 'password', 'sync_date', 'note']
    list_display = ['user', 'email', 'sync_date', 'note']
    ordering = ['user', 'sync_date']
    search_fields = ['user__username', 'email']
    search_help_text = "유저나 화웨이 계정으로 검색할 수 있습니다"


class HealthDataAdmin(admin.ModelAdmin):
    """HealthData 모델 어드민
    """
    list_display = ['fullname', 'date', 'heart', 'sleeps', 'steps', 'stresses', 'blood']
    ordering = ['huami_account', 'date']
    search_fields = ['huami_account__user__username', 'date']
    search_help_text = "유저나 날짜로 검색할 수 있습니다."

    def fullname(self, obj: HealthData):
        return obj.huami_account.fullname

    def heart(self, obj: HealthData):
        return obj.heart_rate is not None

    def sleeps(self, obj: HealthData):
        return obj.sleep_quality is not None

    def steps(self, obj: HealthData):
        return obj.step_count is not None

    def stresses(self, obj: HealthData):
        return obj.stress is not None

    def blood(slef, obj: HealthData):
        return obj.spo2 is not None


admin.site.register(HuamiAccount, HuamiAccountAdmin)
admin.site.register(HealthData, HealthDataAdmin)
