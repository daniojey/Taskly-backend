from rest_framework import serializers

from api.serializers.project_serializers import ProjectSerializer, ProjectWithTasksSerializer
from api.serializers.user_serializers import UserSerializer
from users.models import Group, User


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

        self.include_projects = self.context.get('include_projects', False)
        self.count_tasks = self.context.get('count_tasks', None)

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

        if not self.include_projects:
            return None
        
        if hasattr(obj, 'group_projects'):
            data= ProjectSerializer(obj.group_projects, many=True, context={"no_group": True}).data
            return data
        
        
        if hasattr(obj, 'projects_in_group'):
            if self.context.get('include_tasks', None):
                count = self.context.get('count_tasks', None)

                query = obj.projects_in_group

                if count:
                    data = ProjectWithTasksSerializer(query, many=True,  context={'count_tasks': count}).data
                else:
                    data = ProjectWithTasksSerializer(query, many=True).data
            else:
                data = ProjectSerializer(query, many=True,  context={"no_group": True}).data
            return data
        

class GroupCountProjectsSerializer(serializers.ModelSerializer):
    count_projects = serializers.SerializerMethodField()
    count_members = serializers.SerializerMethodField()

    def get_count_projects(self, obj):
        return obj.count_projects
    
    def get_count_members(self, obj):
        return obj.count_members

    class Meta:
        model = Group
        fields = ['id','name', 'count_projects', 'count_members']


class GroupDetailSerializer(serializers.ModelSerializer):
    projects = ProjectWithTasksSerializer(source="projects_in_group", many=True)
    members = UserSerializer(source="prefetch_members", many=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'projects', 'members']