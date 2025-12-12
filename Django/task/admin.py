from django.contrib import admin

from task.models import Task, TaskComment, TaskImage

# Register your models here.
@admin.register(Task)
class TaskModelAdmin(admin.ModelAdmin):
    pass


@admin.register(TaskComment)
class TaskCommentModelAdmin(admin.ModelAdmin):
    pass

@admin.register(TaskImage)
class TaskImageModelAdmin(admin.ModelAdmin):
    pass
