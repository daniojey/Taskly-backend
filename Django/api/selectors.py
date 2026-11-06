
from django.db.models import Q, Exists, OuterRef

from task.models import Task
from users.models import Group, User

def visible_task(user: User, task_id: str = None):
    filters = Q(user_id=user.id)

    if task_id is not None:
        filters &= Q(task_id=task_id)

    is_performer = Task.performers.through.objects.filter(filters)

    return Task.objects.filter(Exists(is_performer) | Q(created_by_id=user.id)).first()

def visible_group(user):
    is_member = Group.members.through.objects.filter(
        group_id=OuterRef("pk"), user_id=user.id
    )

    return Group.objects.filter(Exists(is_member) | Q(owner_id=user.id))