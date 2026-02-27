from celery import Celery, shared_task
from celery.schedules import crontab
from django.db.models import F, DurationField, ExpressionWrapper
from django.utils import timezone
from django.utils.timezone import timedelta 

from users.models import Group, Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from main.celery import app
from task.models import TaskPerformSession


@shared_task
def sum_strings(data_string: str):
    print(f"THIS A STINGS {data_string}")
    return data_string


@shared_task()
def create_notify_user(user_id: int, type_message: str, notify_message: str, push_message: str, group_id=None):

    Notification.objects.create(
        notify_type=type_message,
        user_id=user_id, 
        message=notify_message,
        data={'group_id': group_id},
    )

    channel = get_channel_layer()

    async_to_sync(channel.group_send)(f'chat_{user_id}', {'type': 'chat_message', 'message': push_message,})


@shared_task()
def create_notify_users(group_id, task_name: str, task_status: str):
    group = Group.objects.get(id=group_id)
    members = list(group.members.all())

    member_list = [
        Notification(user=item, message=f"task: {task_name}: Status changed in {task_status}")
        for item in members
    ]

    Notification.objects.bulk_create(member_list)

    channel = get_channel_layer()

    for item in members:
        async_to_sync(channel.group_send)(f'chat_{item.id}', {'type': 'chat_message', 'message': f'task: {task_name} status Updated', 'datas': 'data1'})


@app.on_after_finalize.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(600.0, update_performers_sessions)


@app.task
def update_performers_sessions(*args, **kwargs):
    sessions = TaskPerformSession.objects.annotate(
        end_ref=ExpressionWrapper(
            timezone.now() - F('updated_at') ,
            output_field=DurationField()
        )
    ).filter(end_ref__gte=timedelta(minutes=10), is_active=True).update(is_active=False)

    print('COMPLETE')