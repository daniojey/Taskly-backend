from rest_framework import serializers

from users.models import Group, User

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

    class Meta:
        model = Group
        fields = ["id", "name", "members", "members_ids"]