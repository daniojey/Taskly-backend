from django.contrib import admin

from task.models import Task, TaskChat, TaskChatMessage

# Register your models here.
@admin.register(Task)
class TaskModelAdmin(admin.ModelAdmin):
    pass


@admin.register(TaskChat)
class TaskChatModelAdmin(admin.ModelAdmin):
    pass

@admin.register(TaskChatMessage)
class TaskChatMessageModelAdmin(admin.ModelAdmin):
    pass
