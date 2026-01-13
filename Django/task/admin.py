from django.contrib import admin

from task.models import Task, TaskComment, TaskImage, TaskPerformSession

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

@admin.register(TaskPerformSession)
class TaskPerformSessionModelAdmin(admin.ModelAdmin):
    pass