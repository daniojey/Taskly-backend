from django.contrib import admin

from .models import GroupLogs, User, Group, Notification

# Register your models here.

@admin.register(Notification)
class NotificationModelAdmin(admin.ModelAdmin):
    pass

@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Group)
class GroupModelAdmin(admin.ModelAdmin):
    pass

@admin.register(GroupLogs)
class GroupLogsModelAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'group', 'created_at' ]
    list_select_related = True