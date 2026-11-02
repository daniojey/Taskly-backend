
from django.db.models import Q, Exists, OuterRef

from task.models import Task
from users.models import Group, User

def visible_task(user: User, task_id: str):
    is_performer = Task.performers.through.objects.filter(
        task_id=task_id, user_id=user.id
    )

    return Task.objects.filter(Exists(is_performer) | Q(created_by_id=user.id))

def visible_group(user):
    is_member = Group.members.through.objects.filter(
        group_id=OuterRef("pk"), user_id=user.id
    )

    return Group.objects.filter(Exists(is_member) | Q(owner_id=user.id))