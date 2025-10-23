import json
from time import sleep
from random import randint
from asgiref.sync import async_to_sync

from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from api.serializers import UserSerializer
from task.models import Task, TaskChat, TaskChatMessage
from users.utils import create_notify_users
from users.models import Group, Notification

class intConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.scope["url_route"]["kwargs"]['int'] = 'base'
        self.room_name = self.scope["url_route"]["kwargs"]["int"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.accept()

    async def receive(self, text_data = None, bytes_data = None):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        user = self.scope['user']
        print('ПОльзователь', user)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"task_chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        user = self.scope['user']

        # groups = await self.get_groups(user)
        # for group in groups:
        #     print(group.name)

        await self.accept()

    @database_sync_to_async
    def get_groups(self, user):
        return list(Group.objects.filter(members__in=[user]))
    
    @database_sync_to_async
    def create_notification(self, task_id, message, user):
        task_chat = TaskChat.objects.get(task__id=task_id)

        TaskChatMessage.objects.create(
            chat=task_chat,
            user=user,
            text=message
        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        user = UserSerializer(self.scope['user']).data
        # print('ПОльзователь', user)

        await self.create_notification(task_id=text_data_json['taskID'], user=self.scope['user'], message=message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message, 'user': user}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        user = event['user']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
                'message': message,
                'user': user
        }))



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