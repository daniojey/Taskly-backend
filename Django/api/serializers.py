from datetime import datetime
from tokenize import group
import attr
from django.db.models import Count
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from users.models import Group, GroupLogs, Notification, User
from task.models import Project, Task, TaskComment


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
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
            'tasks'
        ]

    def validate(self, attrs):

        if 'group' in attrs:
            return super().validate(attrs)
        else:
            raise serializers.ValidationError({
                    'group': 'You are not a member of this group.'
                })
        

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


class UserSerializer(serializers.ModelSerializer):
    image_profile_url = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()
    in_group = serializers.SerializerMethodField()
    is_invite_send = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 
            'first_name', 
            'last_name', 
            'username', 
            'email', 
            'image_profile', 
            'image_profile_url', 
            'last_login',
            'in_group',
            'is_invite_send'
        ]

    def get_image_profile_url(self, obj):

        if obj.image_profile and hasattr(obj.image_profile, 'url'):
            request = self.context.get('request', None)

            if request:
                return request.build_absolute_uri(obj.image_profile.url)
            return obj.image_profile.url
        
    def get_last_login(self, obj):
        
        localtime = timezone.localtime(obj.last_login)
        return localtime.strftime("%m/%d/%Y, %H:%M")
    
    def get_in_group(self, obj):

        if self.context.get('check_in_group', None):
            return obj.in_group
        else:
            return False
        
    def get_is_invite_send(self, obj):
        if self.context.get('check_in_group', None):
            return obj.is_invite_send
        else:
            return False
            

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', {})

        if context:
            is_admin = context.get("is_admin", None)
            if is_admin == False:
                self.fields.pop('id')

            if not context.get('check_in_group', None):
                self.fields.pop('in_group')
                self.fields.pop('is_invite_send')

class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    # members = UserSerializer(many=True, read_only=True)
    members = serializers.SerializerMethodField()

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
        fields = ["id", "name", "members", "members_ids", "projects", 'owner']


    def get_members(self, obj):

        request = self.context.get('request', None)

        if request:
            data = UserSerializer(obj.members.all(), many=True, context={'request': request}).data
        else:
            data = UserSerializer(obj.members.all(), many=True).data

        return data

    
    def get_projects(self, obj):

        if not self.context.get("include_projects", None):
            return None
        
        
        if hasattr(obj, 'group_projects'):
            data= ProjectSerializer(obj.group_projects, many=True, context={"no_group": True}).data
            return data
        
        if hasattr(obj, 'projects'):
            if self.context.get('include_tasks', None):
                count = self.context.get('count_tasks', None)

                query = obj.projects.all().annotate(count_tasks = Count('tasks')).order_by('-count_tasks')

                if count:
                    data = ProjectSerializer(query, many=True,  context={"no_group": True, 'include_tasks': True, 'count_tasks': count}).data
                else:
                    data = ProjectSerializer(query, many=True,  context={"no_group": True, 'include_tasks': True}).data
            else:
                data = ProjectSerializer(query, many=True,  context={"no_group": True}).data
            return data

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
    

class TaskChatMessageSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    images_urls = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', None)
        print(context)

    class Meta:
        model = TaskComment
        fields = ['text', 'user', 'created_at', 'message', 'images_urls']


    def get_user(self, obj):
        user = UserSerializer(obj.user).data

        return user
    
    def get_message(self, obj):
        return obj.text
    
    def get_images_urls(self, obj):
        request = self.context.get('request', None)
        
        if hasattr(obj, 'task_images') and obj.task_images:
            print(obj.task_images)

            urls = []

            for item in obj.task_images:
                if request:
                    urls.append({
                        "id": item.id,
                        'url': request.build_absolute_uri(item.image.url),
                        'filename': item.image.name.split('/')[1]
                    })
                else:
                    urls.append({
                        "id": item.id,
                        'url': item.image.url,
                        'filename': item.image.name.split('/')[1]
                    })
            print(urls)
            return urls

        return []