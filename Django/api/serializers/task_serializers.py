from rest_framework import serializers
from task.models import Task

class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model=Task
        fields = '__all__'
        
        
class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    deadline = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", 
            'project_name',
            'project', 
            'name', 
            'description', 
            'deadline', 
            'created_at', 
            'status'
        ]

    
    def get_project_name(self, obj):
        return obj.project.title
    
    def get_deadline(self, obj):
        return obj.deadline.strftime("%m/%d/%Y | %H:%M")
    
    def get_created_at(self, obj):
        return obj.created_at.strftime("%m/%d/%Y")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', {})

        if "method" in context and context['method'] == 'get':
            self.fields.pop('project')


class ShortTaskSerializer(serializers.ModelSerializer):
    #TODO Сделать укороченый сериализатор для оптимизации

    class Meta:
        model = Task
        fields = [
            "id", 
            'name', 
            'description', 
            'deadline', 
            'created_at', 
            'status'
        ]