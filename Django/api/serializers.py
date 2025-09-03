from datetime import datetime
from tokenize import group
from rest_framework import serializers

from users.models import Group, User
from task.models import Project, Task


class ProjectSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    create_at = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', None)

        if context and "no_group" in context:
            self.fields.pop('group')

        if context and "include_tasks" not in context:
            self.fields.pop('tasks')
            

    def get_group_name(self, obj):
        if obj.group:
            return obj.group.name
        else:
            return None
        
    def get_tasks(self, obj):
        count = self.context.get('count_tasks', None)

        if count:
            data = TaskSerializer(obj.tasks.all()[:count], many=True, context={'method': 'get'}).data
        else:
            data = TaskSerializer(obj.tasks.all(), many=True, context={'method': 'get'}).data
        # print(obj.tasks.all())
        return data 
    
    def get_create_at(self, obj):
        return obj.create_at.strftime("%m/%d/%Y")

    class Meta:
        model = Project
        fields = ["id", 'group',"group_name", "title", "description", 'create_at', 'tasks']

    def validate(self, attrs):
        print(attrs)

        if 'group' in attrs:
            return super().validate(attrs)
        else:
            raise serializers.ValidationError({
                    'group': 'You are not a member of this group.'
                })
        
class TaskSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    deadline = serializers.SerializerMethodField()
    create_at = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["id", 'group','owner','username', 'project_name','project', 'name', 'description', 'deadline', 'create_at']

    def get_username(self, obj):
        return obj.owner.username
    
    def get_project_name(self, obj):
        return obj.project.title
    
    def get_deadline(self, obj):
        return obj.deadline.strftime("%m/%d/%Y")
    
    def get_create_at(self, obj):
        return obj.create_at.strftime("%m/%d/%Y")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', {})

        if "method" in context and context['method'] == 'get':
            self.fields.pop('owner')
            self.fields.pop('project')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email']

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', {})

        if context:
            is_admin = context.get("is_admin", None)
            if is_admin == False:
                self.fields.pop('id')


class GroupSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    members_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=User.objects.all(),
        source="members"
    )

    projects = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', None)

        print(context)

        # if context and context["include_projects"] == True:
            # self.fields.pop('members')
            # self.fields.pop('projects')

    class Meta:
        model = Group
        fields = ["id", "name", "members", "members_ids", "projects"]

    
    def get_projects(self, obj):

        if not self.context.get("include_projects", None):
            return None
        
        
        if hasattr(obj, 'group_projects'):
            data= ProjectSerializer(obj.group_projects, many=True, context={"no_group": True}).data
            return data
        
        if hasattr(obj, 'projects'):
            if self.context.get('include_tasks', None):
                count = self.context.get('count_tasks', None)

                if count:
                    data = ProjectSerializer(obj.projects.all(), many=True,  context={"no_group": True, 'include_tasks': True, 'count_tasks': count}).data
                else:
                    data = ProjectSerializer(obj.projects.all(), many=True,  context={"no_group": True, 'include_tasks': True}).data
            else:
                data = ProjectSerializer(obj.projects.all(), many=True,  context={"no_group": True}).data
            return data
