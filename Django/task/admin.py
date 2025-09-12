from django.contrib import admin

from task.models import Task

# Register your models here.
@admin.register(Task)
class TaskModelAdmin(admin.ModelAdmin):
    pass