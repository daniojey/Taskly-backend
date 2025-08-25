from django.db import models


class Project(models.Model):
    group = models.ForeignKey("users.Group", verbose_name="project_group", on_delete=models.SET_NULL, null=True, related_name="projects") 
    title = models.CharField(max_length=130, verbose_name="project_title")
    description = models.CharField(max_length=500, verbose_name="project_description")
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Project {self.title}"


class Task(models.Model):
    owner = models.ForeignKey("users.User", verbose_name="task_owner", on_delete=models.CASCADE, related_name="owner")
    project = models.ForeignKey("task.Project", verbose_name="task_from_project", on_delete=models.CASCADE, related_name="project")
    name = models.CharField(max_length=130, verbose_name="task_name")
    description = models.CharField(max_length=1000, verbose_name="task_description")
    deadline = models.DateTimeField(verbose_name="task_deadline")
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner} - {self.project} - {self.name}"