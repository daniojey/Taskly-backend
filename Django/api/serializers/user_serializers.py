from rest_framework import serializers
from users.models import User
from rest_framework.serializers import ValidationError
from django.utils import timezone

class CreateUserSerializer(serializers.ModelSerializer):
    confirmPassword = serializers.CharField(write_only=True)

    def validate(self, attrs):
        print(attrs)
        email = attrs.get('email', None)
        password = attrs.get('password', None)
        confirm_password = attrs.pop('confirmPassword', None)

        if email and User.objects.filter(email=email).exists():
            raise ValidationError('email exists')
        
        if not password or not confirm_password:
            raise ValidationError('password and confim password required fields')
        else:
            if password != confirm_password:
                raise ValidationError('passwords not match')

        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'password',
            'email',
            'confirmPassword'
        ]

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