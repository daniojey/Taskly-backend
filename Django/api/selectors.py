
from django.db.models import Q, Exists, OuterRef

from users.models import Group

def visible_group(user):
    is_member = Group.members.through.objects.filter(
        group_id=OuterRef("pk"), user_id=user.id
    )

    return Group.objects.filter(Exists(is_member) | Q(owner_id=user.id))