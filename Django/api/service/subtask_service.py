from api.serializers.subtasks_serializers import CreateSubTaskSerializer
from task.models import Task
from main.utils.custom_api_errors import TaskNotFoundId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError


class SubTaskService:

    @staticmethod
    def create_subtask(self, data, task_id):
        if not task_id:
            raise TaskNotFoundId()

        task = Task.objects.get(id=task_id)
        last_subtask = task.subtask.order_by('-id').first()

        serializer = CreateSubTaskSerializer(data=data, context={'position': last_subtask.id + 1})
        if serializer.is_valid():
            serializer.save()
            return Response({'results': serializer.data}, status=status.HTTP_201_CREATED)
        else:
            raise ValidationError(serializer.errors)