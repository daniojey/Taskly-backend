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
    list_display = [
        'id', 
        'performer',
        'task',
        'duration',
        'is_active',
        'updated_at',
        'created_at',
    ]
    list_display_links = [
        'id',
        'performer'
    ]
    list_select_related = ['performer', 'task']
    list_per_page = 20

    fieldsets = [
        ('Basic', {'fields': ['performer', 'task', 'duration', 'is_active']}),
        ('Dates', {'fields': ['created_at', 'updated_at']}),
    ]
    readonly_fields = ['updated_at', 'created_at']