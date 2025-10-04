from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync, sync_to_async

from users.models import Notification

def create_notify_users(group, task_name: str, task_status: str):
    print('CREATED NOTIFY')
    members = list(group.members.all())

    member_list = [
        Notification(user=item, message=f"task: {task_name}: Status changed in {task_status}")
        for item in members
    ]

    Notification.objects.bulk_create(member_list)

    channel = get_channel_layer()

    for item in members:
        async_to_sync(channel.group_send)(f'chat_{item.id}', {'type': 'chat_message', 'message': f'task: {task_name} status Updated', 'datas': 'data1'})

    print(members)

