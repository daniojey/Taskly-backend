from django.contrib import admin

from .models import User, Group

# Register your models here.
@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Group)
class GroupModelAdmin(admin.ModelAdmin):
    pass