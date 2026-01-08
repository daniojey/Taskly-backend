from rest_framework import serializers
from task.models import TaskComment
from api.serializers.user_serializers import UserSerializer

class TaskChatMessageSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    images_urls = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs.get('context', None)
        print(context)

    class Meta:
        model = TaskComment
        fields = ['id','text', 'user', 'created_at', 'message', 'images_urls', 'answer_to']


    def get_user(self, obj):
        user = UserSerializer(obj.user).data

        return user
    
    def get_message(self, obj):
        return obj.text
    
    def get_images_urls(self, obj):
        request = self.context.get('request', None)
        
        if hasattr(obj, 'task_images') and obj.task_images:
            print(obj.task_images)

            urls = []

            for item in obj.task_images:
                if request:
                    urls.append({
                        "id": item.id,
                        'url': request.build_absolute_uri(item.image.url),
                        'filename': item.image.name.split('/')[1]
                    })
                else:
                    urls.append({
                        "id": item.id,
                        'url': item.image.url,
                        'filename': item.image.name.split('/')[1]
                    })
            print(urls)
            return urls

        return []