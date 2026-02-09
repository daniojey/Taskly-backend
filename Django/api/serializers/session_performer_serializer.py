
from Django.api.serializers.user_serializers import UserSerializer
from task.models import TaskPerformSession
from rest_framework import serializers


class TaskPerformSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskPerformSession
        fields = ['id', 'duration', 'is_active','created_at']


class TaskPerformSessionWithUsersSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='performer')

    class Meta:
        model = TaskPerformSession
        fields = ['id', 'user', 'duration', 'is_active', 'created_at']