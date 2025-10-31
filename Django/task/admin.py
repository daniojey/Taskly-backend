from django.contrib import admin

from task.models import Task, TaskComment

# Register your models here.
@admin.register(Task)
class TaskModelAdmin(admin.ModelAdmin):
    pass


@admin.register(TaskComment)
class TaskCommentModelAdmin(admin.ModelAdmin):
    pass
