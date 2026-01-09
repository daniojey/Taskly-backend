from django.db import models


class Project(models.Model):
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='project_owner')
    group = models.ForeignKey("users.Group", verbose_name="project_group", on_delete=models.SET_NULL, null=True, related_name="projects") 
    title = models.CharField(max_length=130, verbose_name="project_title")
    description = models.CharField(max_length=500, verbose_name="project_description", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Project {self.title}"
    
    class Meta:
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'


class Task(models.Model):
    NO_STATUS = 'NS'
    BASE_STATUS = 'BS'
    URGENT_STATUS = 'US'

    STATUS_TASK = [
        (NO_STATUS, 'No Status'),
        (BASE_STATUS, 'Active task'),
        (URGENT_STATUS, 'Urgent task'),
    ]

    status = models.CharField(choices=STATUS_TASK, verbose_name="task_status")
    created_by = models.ForeignKey("users.User", verbose_name="task_owner", on_delete=models.CASCADE, related_name="owner")
    project = models.ForeignKey("task.Project", verbose_name="task_from_project", on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=130, verbose_name="task_name")
    description = models.TextField(max_length=1000, verbose_name="task_description")
    deadline = models.DateTimeField(verbose_name="task_deadline")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project} - {self.name}"
    
    @property
    def group(self):
        return self.project.group
    
    class Meta:
        db_table = 'Task'
        verbose_name = 'Project task'
        verbose_name_plural = 'Project tasks'
        indexes = [
            models.Index(fields=['project', 'created_at']),
        ]
    

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name='messages')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='user_messages')
    answer_to = models.JSONField(default=list, verbose_name='reply_message')
    text = models.TextField(max_length=1000, verbose_name='text_message')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}:{self.text[:70]}"
    class Meta:
        db_table = 'task_chat_message'
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
    


class TaskImage(models.Model):
    message = models.ForeignKey(TaskComment, on_delete=models.CASCADE ,related_name='message_image')
    title = models.CharField(max_length=155)
    image = models.ImageField(upload_to='task_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        db_table = 'task_image'
        verbose_name = 'Task image'
        verbose_name_plural = 'Task images'
    