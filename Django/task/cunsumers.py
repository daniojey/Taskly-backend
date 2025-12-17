import json
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.files.base import ContentFile
from django.db.models import Prefetch

from api.serializers import TaskChatMessageSerializer, UserSerializer
from task.models import Task, TaskComment, TaskImage
from users.utils import create_notify_users
from users.models import Group, Notification


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_files = {}

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"task_chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    
    async def receive(self, text_data = None, bytes_data = None):
        
        if text_data:
            data = json.loads(text_data)
            print(data)
            message_type = data.get('type')

            if message_type == 'message_metadata':
                message= await self.create_notification(data)
                print(message)
                self.pending_files[data['messageId']] = {
                    'message': message['data'],
                    'files': [],
                    'expected_count': data['filesCount']
                }

            elif message_type == 'file_metadata':
                message_id = data['messageId']
                if message_id in self.pending_files:
                    self.pending_files[message_id]['files'].append({
                        'metadata': data,
                        'data': None
                    })

            elif message_type == 'message_complete':
                message_id = data['messageId']
                await self.save_message_files(message_id)
                user = UserSerializer(self.scope['user']).data
                actual_message = await self.get_updated_message(self.pending_files[message_id]['message'].id)
                print(actual_message)
                print(actual_message.task_images)
                await self.channel_layer.group_send(
                    self.room_group_name, {"type": "chat.message", "message": TaskChatMessageSerializer(actual_message).data, 'user': user}
                )

        elif bytes_data:
            for message_id, pending in self.pending_files.items():
                for file_info in pending['files']:
                    if file_info['data'] is None:
                        file_info['data'] = bytes_data
                        break

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        user = event['user']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
                'message': message,
                'user': user
        }))

    @database_sync_to_async
    def get_updated_message(self, message_id):
        return TaskComment.objects.select_related('user').prefetch_related(
            Prefetch(
                'message_image',
                queryset=TaskImage.objects.all(),
                to_attr='task_images'
            )
        ).get(id=message_id)

    @database_sync_to_async
    def get_groups(self, user):
        return list(Group.objects.filter(members__in=[user]))
    
    
    @database_sync_to_async
    def create_notification(self, data):

        if 'answerToMessage' in data:
            answer_message_data = {
                'id': data['answerToMessage'].get('id'),
                'text': data['answerToMessage'].get('text')
            }
            print('MEssage dataas',answer_message_data)
        else:
            answer_message_data = {}

        try:
            created = TaskComment.objects.create(
                task_id=data['taskId'],
                user=self.scope['user'],
                text=data['message'],
                answer_to=answer_message_data
            )

            return {"type":'success', 'data': created}
        
        except Task.DoesNotExist:
                return {"type":'error', "message": 'Not Task Chat model exists'}

    @sync_to_async
    def save_message_files(self, message_id):
        if message_id not in self.pending_files:
            return
        
        pending = self.pending_files[message_id]
        message = pending['message']

        print(self.pending_files)

        for file_info in pending['files']:
            metadata = file_info['metadata']
            file_data = file_info['data']

            if file_data:
                file_obj = ContentFile(file_data, name=metadata['fileName'])
                TaskImage.objects.create(
                    message=message,
                    image=file_obj
                )
        
        

class NotifiConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope['user']
        print(user)

        if user.is_authenticated:
            print('ПОЛЬЗОВАТЕЛЬ АУТЕНТИФИЦИРОВАН')
            await self.channel_layer.group_add(f'chat_{user.id}', self.channel_name)
            await self.accept()

        
    async def chat_message(self, event):
        message = event.get('message', None)
        task_id = event.get('task_id', None)

        if task_id:
            print("СОобщение ", message)
            user = self.scope['user']
            members = await self.get_groups(task_id=task_id)


        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def get_groups(self, task_id):
        task = Task.objects.select_related('group').get(id=task_id)

        print(task.group)

        members = task.group.members.all()

        print(members)