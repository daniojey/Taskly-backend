from django.utils import timezone
from rest_framework import serializers

from users.models import GroupLogs

class GroupLogsSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    anchor_username = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = GroupLogs
        fields = [
            'event', 
            'event_type', 
            'group_name', 
            'anchor_username',
            'created_at', 
            'data'
        ]

    def get_group_name(self, obj):
        return obj.group.name
    
    def get_anchor_username(self, obj):
        if obj.anchor:
            return obj.anchor.username
        
    def get_created_at(self, obj):
        localtime = timezone.localtime(obj.created_at)
        return localtime.strftime("%H:%M:%S %d.%m.%Y")
        