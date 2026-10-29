from users.models import Notification
from api.tasks import create_notify_users
from main.settings import IS_ENABLE_CELERY
from main.utils.custom_api_errors import ForbiddenAPIException, TaskCreateNotValidData, TaskNotFoundId, TaskUpdateNotValidData
from task.models import Project, Task
from api.serializers.task_serializers import TaskCreateSerializer, TaskSerializer
from rest_framework.serializers import ReturnDict

class TaskService:

    @staticmethod
    def create_task(request, project_id: Project):
        data = request.data
        data['project'] = project_id
        data['created_by'] = request.user.id if hasattr(request, 'user') else None

        serializer = TaskCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return serializer.data
        else:
            raise TaskCreateNotValidData(serializer.errors)

    @staticmethod
    def partial_update_task(request, instance: Task):

        if instance.owner.id != request.user.id:
            raise ForbiddenAPIException

        serializer = TaskSerializer(
            instance,
            data=request.data,
            partial=True,
            context={'method': 'path'}
        )

        if serializer.is_valid():
            serializer.save()
            return
        else:
            raise TaskUpdateNotValidData(serializer.errors)

    @staticmethod
    def update_task_status(request, task: Task):
        data = request.data

        new_status = data.get('new_status', None)

        if new_status and task.status != new_status:
            task.status = new_status
            task.save()

        if IS_ENABLE_CELERY:
            create_notify_users.delay(
                notify_type=Notification.TASK_UPDATE_MESSAGE,
                group_id=task.group.id, 
                task_name=task.name, 
                task_status=task.status
            )
        else:
            create_notify_users(
                notify_type=Notification.TASK_UPDATE_MESSAGE,
                group_id=task.group.id, 
                task_name=task.name, 
                task_status=task.status
            )
