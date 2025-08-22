from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField(verbose_name="user", max_length=130, unique=True)

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField("User", verbose_name="user_profile", on_delete=models.CASCADE, related_name="userprofile")

    def __str__(self):
        return f"{self.user.username} Profile"
    

class Group(models.Model):
    name = models.CharField(max_length=130, verbose_name="group_name")
    members = models.ManyToManyField("users.User", verbose_name="group_members", related_name="user_groups")

    def __str__(self):
        return self.name
    



