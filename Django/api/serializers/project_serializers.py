from rest_framework import serializers
from api.serializers.task_serializers import TaskSerializer
from task.models import Project

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', None)

        if context and "no_group" in context:
            self.fields.pop('group')
            

    def get_group_name(self, obj):
        if obj.group:
            return obj.group.name
        else:
            return None
        
    def get_created_at(self, obj):
        return obj.created_at.strftime("%m/%d/%Y")

    class Meta:
        model = Project
        fields = [
            "id", 
            'group',
            "group_name", 
            "title", 
            "description", 
            'created_at', 
        ]

    def validate(self, attrs):

        if 'group' in attrs:
            return super().validate(attrs)
        else:
            raise serializers.ValidationError({
                    'group': 'You are not a member of this group.'
                })
        
class ProjectWithTasksSerializer(ProjectSerializer):
    tasks = TaskSerializer(source='project_tasks', many=True)

    class Meta:
        model = Project
        fields = [
            "id", 
            "title", 
            "description", 
            'created_at', 
            'tasks'
        ]