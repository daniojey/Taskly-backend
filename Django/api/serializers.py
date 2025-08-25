from tokenize import group
from rest_framework import serializers

from users.models import Group, User
from task.models import Project, Task


class ProjectSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()

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

    class Meta:
        model = Project
        fields = ["id", 'group',"group_name", "title", "description", 'create_at']

    def validate(self, attrs):
        if hasattr(attrs, 'group'):
            return super().validate(attrs)
        else:
            raise serializers.ValidationError({
                    'group': 'You are not a member of this group.'
                })

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

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

        if context and context["include_projects"] == True:
            self.fields.pop('members')

    class Meta:
        model = Group
        fields = ["id", "name", "members", "members_ids", "projects"]

    
    def get_projects(self, obj):

        if not self.context.get("include_projects", None):
            return None
        
        
        if hasattr(obj, 'group_projects'):
            return ProjectSerializer(obj.group_projects, many=True, context={"no_group": True}).data
        
