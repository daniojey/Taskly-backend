
from api.serializers.user_serializers import UserSerializer
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


class SessionSerializerWithDate(serializers.ModelSerializer):
    user = UserSerializer(source='performer')
    created_at = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = TaskPerformSession
        fields = ['id', 'user', 'duration', 'is_active', 'created_at']

    def get_created_at(self, obj):
        return obj.created_at.strftime("%B")
    
    def get_duration(self, obj):
        return obj.duration.total_seconds()