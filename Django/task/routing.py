from django.urls import re_path

from . import cunsumers

websocket_urlpatterns = [
    re_path(r"ws/int/$", cunsumers.intConsumer.as_asgi()),
    re_path(r"ws/notifi/$", cunsumers.NotifiConsumer.as_asgi()),
    re_path(r"ws/chat/(?P<room_name>\w+)/$", cunsumers.ChatConsumer.as_asgi()),
]