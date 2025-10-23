from django.db import models


class Project(models.Model):
    group = models.ForeignKey("users.Group", verbose_name="project_group", on_delete=models.SET_NULL, null=True, related_name="projects") 
    title = models.CharField(max_length=130, verbose_name="project_title")
    description = models.CharField(max_length=500, verbose_name="project_description")
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Project {self.title}"


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
    group = models.ForeignKey("users.Group", verbose_name="project_group", on_delete=models.CASCADE, related_name="tasks") 
    owner = models.ForeignKey("users.User", verbose_name="task_owner", on_delete=models.CASCADE, related_name="owner")
    project = models.ForeignKey("task.Project", verbose_name="task_from_project", on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=130, verbose_name="task_name")
    description = models.CharField(max_length=1000, verbose_name="task_description")
    deadline = models.DateTimeField(verbose_name="task_deadline")
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner} - {self.project} - {self.name}"
    

class TaskChat(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, verbose_name='chat')


    class Meta:
        db_table = 'chat_task'
        verbose_name = 'Task Chat'
        verbose_name_plural = 'Task Chats'



class TaskChatMessage(models.Model):
    chat = models.ForeignKey(TaskChat, on_delete=models.CASCADE, verbose_name='messages')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='user_messages')
    text = models.CharField(max_length=700, verbose_name='text_message')
    date_add = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_chat_message'
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'