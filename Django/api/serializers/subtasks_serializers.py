from rest_framework.serializers import ModelSerializer

from task.models import SubTask

class CreateSubTaskSerializer(ModelSerializer):

    class Meta:
        model = SubTask
        fields = ['task', 'title', 'description']