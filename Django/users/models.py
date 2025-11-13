from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    image_profile = models.ImageField(verbose_name='image_profile', upload_to='media/', null=True, blank=True)
    username = models.CharField(verbose_name="user", max_length=130, unique=True)

    def __str__(self):
        return self.username
    
    class Meta:
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"


class Notification(models.Model):
    INVITE_MESSAGE = 'Invite'
    TASK_UPDATE_MESSAGE = 'Task status update'

    TYPE_MESSAGES = [
        (INVITE_MESSAGE, 'Invite'),
        (TASK_UPDATE_MESSAGE, 'Task status update'),
    ]

    notify_type = models.CharField(choices=TYPE_MESSAGES, verbose_name='message type')
    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='user')
    message = models.TextField(max_length=500, verbose_name='text')
    group_id = models.JSONField(verbose_name='group_id', blank=True, null=True)                     
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='created date')
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"user: {self.user}, message: {self.message}"
    
    class Meta:
        db_table = 'notify'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'


class Profile(models.Model):
    user = models.OneToOneField("User", verbose_name="user_profile", on_delete=models.CASCADE, related_name="userprofile")
    
    def __str__(self):
        return f"{self.user.username} Profile"
    

class Group(models.Model):
    owner = models.ForeignKey(User,on_delete=models.CASCADE, verbose_name='owner', related_name='groups_owner')
    name = models.CharField(max_length=130, verbose_name="group_name")
    members = models.ManyToManyField("users.User", verbose_name="group_members", related_name="user_groups")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "group"
        verbose_name = "Group"
        verbose_name_plural = "Groups"


