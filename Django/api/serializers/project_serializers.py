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
    tasks = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.task_count = self.context.get('task_count', False)


    class Meta:
        model = Project
        fields = [
            "id", 
            'group',
            "group_name", 
            "title", 
            "description", 
            'created_at', 
            'tasks'
        ]

    def get_tasks(self, obj):
        if hasattr(obj, 'project_tasks'):
            
            if self.task_count:
                data = TaskSerializer(obj.project_tasks[:self.task_count], many=True).data
            else:
                data = TaskSerializer(obj.project_tasks, many=True).data
        
            return data
    
        return None