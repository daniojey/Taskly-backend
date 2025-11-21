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
    data = models.JSONField(verbose_name='group_id', blank=True, null=True)                     
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


class GroupLogsQueryset(models.QuerySet):
    
    def optimized(self):

        return self.select_related(
            'group', 'anchor'
        ).only(
            'event',
            'event_type',
            'group__name',
            'group__owner',
            'created_at',
            'anchor__username'
        )

class GroupLogsManager(models.Manager):

    def get_queryset(self):
        return GroupLogsQueryset(self.model, using=self._db)

    def group_select(self, group_id):
        return self.get_queryset().filter(group__id=group_id)


class GroupLogs(models.Model):
    ADD_MEMBER = 'Add member'
    KICKED_MEMBER = 'Kicked member'
    CHANGE_SETTINGS = 'Change settings'
    INVITE_MEMBER = 'Invite member'
    INVITE_DEFLECTED = 'Invite deflected'

    TYPE_EVENTS = [
        (ADD_MEMBER, 'Add member'),
        (KICKED_MEMBER, 'Kicked Member'),
        (CHANGE_SETTINGS, 'Change settings'),
        (INVITE_MEMBER, 'Invite member'),
        (INVITE_DEFLECTED, 'Invite deflected')
    ]


    event = models.CharField(max_length=200, verbose_name='triggered event')
    event_type = models.CharField(choices=TYPE_EVENTS, verbose_name="event type")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='logs', verbose_name='logs')
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict, verbose_name='log_data', null=True)
    anchor = models.ForeignKey('User', null=True, on_delete=models.SET_NULL, verbose_name='event_triggered', related_name='log_anchor')


    objects = models.Manager()
    logmanager = GroupLogsManager()

    def __str__(self):
        return self.event_type

    class Meta:
        db_table = 'group_logs'
        verbose_name = 'GroupLog'
        verbose_name_plural = 'GroupLogs'



