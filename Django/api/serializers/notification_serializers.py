from rest_framework import serializers
from  django.utils import timezone
from users.models import Notification
from api.serializers.user_serializers import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):

    user = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    group_id = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'message', 'created_at', 'user', 'notify_type', 'group_id']


    def get_user(self, obj):
        user = UserSerializer(obj.user).data
        return user
    
    def get_created_at(self, obj):
        localtime = timezone.localtime(obj.created_at)
        return localtime.strftime("%m/%d/%Y, %H:%M")
    
    def get_group_id(self, obj):

        if isinstance(obj.data, dict):
            return obj.data.get('group_id', None)
        return None
    