from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import serializers

from huami.models import HuamiAccount
from huami.models.healthdata import HealthData
from survey.models.survey import Survey
from survey.models.user_survey import UserSurvey


class UserSurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSurvey
        fields = ['survey_name', 'counts']


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = ['title']


class HuamiHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthData
        fields = ['date', 'info_status']


class HuamiSerializer(serializers.ModelSerializer):
    last_health_info = HuamiHealthSerializer()

    class Meta:
        model = HuamiAccount
        fields = ['fullname', 'note', 'sync_date', 'last_health_info']


class UserSerializer(serializers.ModelSerializer):
    huami = HuamiSerializer(read_only=True)
    user_survey = UserSurveySerializer(UserSurvey.objects.aggregate(counts=Count('survey')), many=True)

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'huami', 'user_survey']


class NormalUserSerializer(serializers.ModelSerializer):
    huami = HuamiSerializer()
    user_survey = UserSurveySerializer(UserSurvey.objects.aaggregate('survey'), many=True)

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'huami', 'user_survey']
