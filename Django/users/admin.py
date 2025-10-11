from django.contrib import admin

from .models import User, Group, Notification

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