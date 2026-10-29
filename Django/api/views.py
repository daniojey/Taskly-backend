import mimetypes
from re import S
from anyio.lowlevel import D
from asgiref.sync import async_to_sync
from decouple import config
from django.conf import settings
from django.db import transaction
from django.utils.timezone import timedelta
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from django.http import FileResponse, JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.db.models import Q, BooleanField, Case, Count, Prefetch, Exists, OuterRef, Value, When
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.views import TokenVerifyView, TokenObtainPairView, TokenRefreshView
from rest_framework.exceptions import ValidationError



from api.permissions.core_permissions import IsTaskOwner, OwnerOrReadOnly
from api.serializers.subtasks_serializers import CreateSubTaskSerializer
from api.service.group_service import GroupService
from api.service.token_service import JWTTokenService
from main.utils.custom_api_errors import ForbiddenAccessSubTasks, NotFoundData, NotFoundProjectId, NotFoundRefreshToken, TaskNotFoundId
from api.serializers.stratagems_serializers import StratagemCreateSerializer, StratagemShortSerializer
from common.cache_managers.project_cache import ProjectCacheManager
from api.serializers.session_performer_serializer import SessionSerializerWithDate, TaskPerformSessionSerializer, TaskPerformSessionWithUsersSerializer
from common.cache_managers.group_cache import GroupCacheManager
from main import settings
from api.utils import GroupLogger
from common.mixins import CacheMixin
from  main.settings import IS_ENABLE_CELERY
from users.models import Group, GroupLogs, Notification, User
from api.tasks import create_notify_user, create_notify_users
from task.models import ActiveTask, Project, Stratagem, SubTask, Task, TaskComment, TaskImage, TaskPerformSession
from .serializers.group_logs_serializers import GroupLogsSerializer
from .serializers.notification_serializers import NotificationSerializer
from .serializers.task_chat_serializers import TaskChatMessageSerializer, TaskimageSerializer
from .serializers.task_serializers import ActiveTaskSerializer, SubTaskSerializer, TaskCreateSerializer, TaskSerializer
from .serializers.user_serializers import CreateUserSerializer, UserPerformerSerializer, UserSerializer
from .serializers.group_serializers import GroupCreateSerializer, GroupDetailSerializer, GroupSerializer, GroupCountProjectsSerializer
from api.paginators import ChatMessagePaginator, GroupLogsPaginator, NotificationPaginator, PerformerSessionsPaginator
from .serializers.project_serializers import (
    ProjectCreateSerializer, 
    ProjectSerializer, 
    ProjectWithTasksSerializer, 
    ProjectWithoutTasksSerializer
)
from api.service.task_service import TaskService



from django.views.decorators.csrf import ensure_csrf_cookie
from google import genai
from google.genai import types

@ensure_csrf_cookie
def csrf(request, *args, **kwargs):
    csrf_token = get_token(request)
    response = JsonResponse({'csrfToken': 'ok'})
    response.set_cookie(
        'csrftoken',
        csrf_token,
        max_age=3600,
        secure=settings.CSRF_COOKIE_SECURE,
        samesite=settings.CSRF_COOKIE_SAMESITE,
    )
    return response


class CustomTokenPairView(TokenObtainPairView):

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        return JWTTokenService.token_pair(request, response)


class CustomTokenRefreshView(TokenRefreshView):

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')

        if not refresh_token:
            raise NotFoundRefreshToken()
        
        data = request.data.copy()
        data['refresh'] = refresh_token
        
        request._full_data = data
        
        response = super().post(request, *args, **kwargs)

        return JWTTokenService.token_refresh(response)
    
class LogoutTokenApiView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response({'results': 'Logout success'}, status=status.HTTP_200_OK)
        refresh_token = request.COOKIES.get('refresh')

        if refresh_token:
            response.delete_cookie('refresh')

        return response

class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        token = request.data.get('token')

        return JWTTokenService.check_token(token)


class UserProfileAPiView(APIView):

    def get(self, request,  *args, **kwargs):
        if self.request.user.is_authenticated:
            user = User.objects.get(id=self.request.user.id)
            serializer = UserSerializer(user, context={'is_admin': self.request.user.is_superuser})

            return Response({"user": serializer.data if serializer != None else "None"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Error"}, status=status.HTTP_400_BAD_REQUEST)


class UserGroupApiView(CacheMixin, viewsets.ViewSet):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [OwnerOrReadOnly, IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        filter_projects = request.GET.get('f', '')
        user = self.request.user
        
        result = GroupService.get_list_queryset(
            request=request,
            filter_projects=filter_projects,
            user=user,
            cache_mixin=self.set_get_cache
        )

        return result
    
    def retrieve(self, request, pk=None, *args, **kwargs):
        user = request.user

        cache_data = self.get_cache(f"group_{pk}_user_{user.id}")
            
        if cache_data:
            return Response({"results": cache_data}, status=status.HTTP_200_OK)

        result = GroupService.get_group(
            request,
            user,
            self.set_cache,
            pk
        )  

        return result
        
    def create(self, request, *args, **kwargs):
        group_data = request.data

        result = GroupService.group_create(
            request,
            group_data
        )

        return result
    

    def delete(self, request, pk=None, *args, **kwargs):
        group = get_object_or_404(Group.objects.select_related('owner'), id=pk)

        self.check_object_permissions(request, group)

        result = GroupService.group_delete(group, request)
        return result
    
    @action(detail=True, methods=['post'])
    def user_invite_group(self, request, pk, *args, **kwargs):
        data = request.data

        result = GroupService.user_invite_group(data, request, pk)

        return result
        
    @action(detail=True, methods=['post'])
    def processing_group_invite(self, request, pk=None, *args, **kwargs):        
        result = GroupService.processing_group_invite(request, pk)
        return result
            
    @action(detail=True, methods=['post'])
    def delete_member(self, request, pk=None, *args, **kwargs):

        result = GroupService.delete_member(
            request,
            pk,
            self.check_permissions
        )

        return result
      
            

class GroupProjectViewSet(CacheMixin,viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = get_object_or_404(Project.objects.select_related("group"), pk=self.kwargs.get('pk', None))
        return obj

    def list(self, request, *args, **kwargs):
        user = self.request.user
        
        cache_data = self.get_cache(f"projects_list_{user.id}")

        if cache_data:
            return Response({"result": cache_data}, status=status.HTTP_200_OK)

        queryset = request.user.user_groups.prefetch_related(
            Prefetch(
                "projects",
                queryset=Project.objects.all().select_related("group"),
                to_attr="group_projects"
            )
        ).all()


        serializer = GroupSerializer(queryset, many=True, context={"include_projects": True})

        self.set_cache(serializer.data, f'projects_list_{user.id}')

        return Response({"result": serializer.data}, status=status.HTTP_200_OK)


    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = ProjectCreateSerializer(data=data)

        GroupCacheManager.clean_group_list_cache(
            filters=['A-z', 'Z-a', 'created', ''],
            user_id=request.user.id
        )

        ProjectCacheManager.clear_all_cache(user_id=request.user.id
)

        if serializer.is_valid():
            serializer.save()

            return Response({'message': serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'error', "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(methods=['get'], detail=True)
    def get_group_projects(self, request, pk=None, *args, **kwargs):
        if pk is None:
            return Response({'results': 'Without group Id'}, status=status.HTTP_404_NOT_FOUND)
        
        group =  Group.objects.select_related('owner').prefetch_related('members', 'projects').get(id=pk)

        if not group:
            return Response({'results': 'Not found group'}, status=status.HTTP_404_NOT_FOUND)
        
        user = request.user

        if user not in group.members.all() or user != group.owner:
            return Response({'results': 'access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        projects = group.projects.all()

        serializer = ProjectWithoutTasksSerializer(projects, many=True)

        return Response({'results': serializer.data}, status=status.HTTP_200_OK)


    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = Project.objects.select_related(
                'group'
            ).prefetch_related(
                Prefetch(
                    'tasks',
                    queryset=Task.objects.all().annotate(
                        is_performer=Exists(
                            User.objects.filter(
                                pk=request.user.pk,
                                assigned_tasks=OuterRef("pk"),
                            )
                        )
                    ),
                    to_attr='project_tasks'
                )
            ).get(pk=pk)


            if not obj:
                return Response({'message': '404'}, status=status.HTTP_404_NOT_FOUND)
            
            if obj.group and obj.group.id in request.user.user_groups.all():
                return Response({'message': "403"}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = ProjectWithTasksSerializer(obj)

            print(serializer.data)
            return Response({"result": serializer.data}, status=status.HTTP_200_OK)
        
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = ProjectSerializer(
            instance,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message":"Project partially updated!", 'result': serializer.data},
                status=status.HTTP_200_OK
            )
        
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if pk:
            try: 
                project = Project.objects.get(id=pk)
            except Project.DoesNotExist as e:
                return Response({'message': 'error delete project'}, status=status.HTTP_400_BAD_REQUEST)
            project.delete()

            return Response({"message": "success delete project"}, status=status.HTTP_204_NO_CONTENT)


class TaskViewSet(viewsets.GenericViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Task.objects
            .filter(project__group__members=user)
            .select_related('owner', 'project')
            .annotate(is_active=Exists(
                ActiveTask.objects.filter(task=OuterRef('pk'), user=user)
            ))
        )

        project_id = self.kwargs.get('project_id')
        return qs.filter(project_id=project_id) if project_id else qs


    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), IsTaskOwner()]
        return super().get_permissions()


    def get_serializer_class(self):
        return {'list': TaskSerializer}.get(self.action, TaskSerializer)


    def get_project_id(self):
        project_id = self.request.data.get("project_id", None)

        if project_id:
            return project_id
        else:
            raise NotFoundProjectId
    
    def create(self, request, *args, **kwargs):
        project_id = self.get_project_id()

        result = TaskService.create_task(
            request=request, 
            project_id=project_id
        )

        return Response({"results": result}, status=status.HTTP_201_CREATED)
        
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        TaskService.partial_update_task(request, instance)

        return Response({'results': "Task update complete"})

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        serializer = TaskSerializer(queryset, many=True, context={"method": "get"})

        return Response({'result': serializer.data, 'project': kwargs.get('project_id', None)}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None, *args, **kwargs):
        task = Task.objects.get(pk=pk)

        TaskService.update_task_status(request, task)

        return Response({'result': task.status}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        return Response({'results': self.get_serializer(self.get_object()).data})
        
    def destroy(self, request, pk=None, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(methods=['get'], detail=False)
    def get_active_tasks(self, request, *args, **kwargs):
        user = request.user
        tasks = ActiveTask.objects.select_related('task', 'task__project').filter(user=user)
        serializer = ActiveTaskSerializer(tasks, many=True)
        return Response({ 'results': serializer.data}, status=status.HTTP_200_OK)
    
    @action(methods=['get', 'put', 'delete'], detail=True)
    def active(self, request, pk=None):
        task = self.get_object()

        if request.method == "GET":
            active_task = ActiveTask.objects.filter(task=task).exists()
            return Response({'results': active_task}, status=status.HTTP_200_OK)
        elif request.method == 'PUT':
            ActiveTask.objects.get_or_create(user=request.user, task=task)
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif request.method == 'DELETE':
            ActiveTask.objects.filter(user=request.user, task=task).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubTaskViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def task_check_exists(self, task_id):
        task = Task.objects.filter(id=task_id).exists()
        print(task)

        if not task:
            raise TaskNotFoundId

    @action(methods=['get'], detail=True)
    def get_subtasks(self, request, pk=None, *args, **kwargs):
        self.task_check_exists(task_id=pk)

        subtasks = SubTask.objects.filter(
            task_id=pk,
            task__project__group__members=request.user
        ).order_by('position')
        serializer = SubTaskSerializer(subtasks, many=True)

        return Response({'results': serializer.data}, status=status.HTTP_200_OK)
        
    def create(self, request, *args, **kwargs):
        data = request.data
        task_id = data.get("task", None)

        if not task_id:
            raise TaskNotFoundId

        task = Task.objects.get(id=task_id)
        last_subtask = task.subtasks.order_by("-id").first()


        serializer = CreateSubTaskSerializer(data=data, context={'position': last_subtask.id + 1})
        if serializer.is_valid():
            serializer.save()
            return Response({'results': serializer.data}, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            raise ValidationError

    def partial_update(self, request, pk, *args, **kwargs):
        instance = SubTask.objects.get(pk=pk)

        serializer = SubTaskSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({'results': serializer.data},status=status.HTTP_200_OK)

    @action(methods=["post"],detail=False)
    def reorder(self, request, *args, **kwargs):
        task_id = request.data.get("task_id", None)
        ordering_ids = request.data.get('reorder', None)

        if not ordering_ids:
            raise NotFoundData

        if not task_id:
            raise TaskNotFoundId

        task = Task.objects.get(id=task_id)
        
        with transaction.atomic():
            subtasks = list(
                task.subtasks.select_for_update().filter(task=task)
            )
            
            by_id = {s.id: s for s in subtasks}
            
            if len(ordering_ids) != len(set(ordering_ids)) or set(ordering_ids) != by_id.keys():
                raise ValidationError({"order": 'Invalid subtask ids'})

            
            changed = []
            for index, subtask_id in enumerate(ordering_ids):
                subtask  = by_id[subtask_id]
                if subtask.position != index:
                    subtask.position = index
                    changed.append(subtask)

            if changed:
                SubTask.objects.bulk_update(changed, ['position'])


        return Response({'results': 'ok'}, status=status.HTTP_200_OK)


    def destroy(self, request, pk=None, *args, **kwargs):
        subtask = SubTask.objects.prefetch_related(
            Prefetch(
                "task",
                queryset=Task.objects.select_related("created_by").all(),
                to_attr="task_owner"
            )
        ).get(pk=pk)

        print(subtask.task_owner.created_by)

        if subtask.task_owner.created_by.id != request.user.id:
            raise ForbiddenAccessSubTasks

        
        subtask.delete()

        return Response({'results': "SubTask Deleted"}, status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(CacheMixin, viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = self.request.user

        query = Notification.objects.select_related('user').filter(user=request.user).order_by('-created_at')

        notifications = self.set_get_cache(query, f'notifications_user_{user}', 60)

        paginator = NotificationPaginator()

        result = paginator.paginate_queryset(notifications, request)

        if result:
            serializer = NotificationSerializer(result, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        return Response({'result': []}, status=status.HTTP_200_OK)
    
    
class ChatMessagesListView(ListAPIView):
    pagination_class = ChatMessagePaginator
    serializer_class = TaskChatMessageSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        # task = get_object_or_404(Task, id=self.kwargs.get('task_id', None))
        # print(task)
        print('LOADING CHAT')
        return TaskComment.objects.filter(task__id=self.kwargs.get('task_id', None)).select_related('user').prefetch_related(
            Prefetch(
                'message_image',
                queryset=TaskImage.objects.all().only('message', 'image'),
                to_attr='task_images'
            )
        )

        # try:
        #     chat = TaskChat.objects.get(task__pk=self.kwargs['chat_id'])
        # except TaskChat.DoesNotExist:
        #     raise NotFound(detail={'message': 'ChatNotExists'})
        
        # return TaskChatMessage.objects.select_related('user').filter(chat=chat)

class ChatMessageImagesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes  = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('images')

        if not files:
            return Response({"results": "Not found files"}, status=status.HTTP_404_NOT_FOUND)

        images = [
            TaskImage(title="", image=file)
            for file in files
        ]

        created_images = TaskImage.objects.bulk_create(images)

        serializer = TaskimageSerializer(created_images, many=True, context={"request": request})
        return Response({'results': serializer.data})


class UserViewSet(viewsets.ViewSet):

    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = CreateUserSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            serializer_data = UserSerializer(user).data
            return Response({'results': serializer_data}, status=status.HTTP_200_OK)
        else:
            return Response({'results': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        

    @action(methods=['post'], detail=False)
    def search_users(self, request, *args, **kwargs):
        data = request.data
        group_id = data.get('group_id', None)
        username = data.get('username', None)

        match (username, group_id):
            case (str() as username, str()) if username:
                users = User.objects.filter(username__icontains=username).annotate(
                in_group=Exists(Group.objects.filter(
                        id=group_id,
                        members=OuterRef('pk')
                    )),

                    is_invite_send=Exists(Notification.objects.filter(
                        user=OuterRef('pk'),
                        data__group_id=int(group_id),
                        notify_type=Notification.INVITE_MESSAGE
                    ))
                )

                serializer = UserSerializer(users, context={
                    'request': request, 
                    'check_in_group': True,
                }, many=True)

                return Response({'results': serializer.data}, status=status.HTTP_200_OK)

            case (str() as username, None) if username:
                print(username)
                users = User.objects.filter(username__icontains=username)

                serializer = UserSerializer(users, context ={
                    'request': request,
                }, many=True)

                return Response({'results': serializer.data}, status=status.HTTP_200_OK)
            
            case _:
                return Response({ 'results': 'Error: not valid data in post'}, status=status.HTTP_400_BAD_REQUEST)
        

class GroupLogsViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes  = [IsAuthenticated]


    def list(self, request, *args, **kwargs):
        queries = request.GET
        group_id = kwargs.get('group_id', None)

        if not group_id:
            return Response({'errors': 'Not group Id'}, status=status.HTTP_400_BAD_REQUEST)
        
        group = Group.objects.select_related('owner').only(
            'owner__id'
        ).get(id=group_id)

        if group.owner.id != request.user.id:
            return Response({'errors': ''}, status=status.HTTP_403_FORBIDDEN)
        
        logs = GroupLogs.logmanager.group_select(group_id=group_id)

        if queries:
            logs = GroupLogs.logmanager.filter_queries(logs, queries)

        paginator = GroupLogsPaginator()

        result = paginator.paginate_queryset(logs, request)

        if result:
            serializer = GroupLogsSerializer(result, many=True)
            return paginator.get_paginated_response(serializer.data)

        else:
            return Response({'results': []}, status=status.HTTP_200_OK)

class DownloadChatImagesView(APIView):
    def get(self, request, message_id, *args, **kwargs):
        message = get_object_or_404(TaskImage, id=message_id)

        if not message:
            return Response({'errors': 'image not found'}, status=status.HTTP_404_NOT_FOUND)
        

        mime_type, _ = mimetypes.guess_type(message.image.path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        response = FileResponse(
            message.image.open('rb'),
            as_attachment=False,
            content_type=mime_type,
            filename=message.image.name.split('/')[-1]
        )

        response['Content-Length'] = message.image.size
        response.headers['content-disposition'] = message.image.name
        return response
    

class TaskPerformersViewSets(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes  = [IsAuthenticated]

    def retrieve(self, request, pk=None, *args, **kwargs):
        data = []

        return Response({ 'results': data}, status=status.HTTP_200_OK)
    
    @action(methods=['get'], detail=True)
    def group_performers(self, request, pk=None, *args, **kwargs):
        group_id = request.GET.get('group', None)

        if not group_id:
            return Response({ 'results': "undefined group" }, status=status.HTTP_400_BAD_REQUEST)

        try:
            group_owner = Group.objects.filter(id=group_id).values_list('owner__id', flat=True).first()
        except Group.DoesNotExist:
            return Response({'results': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.id != group_owner:
            return Response({ 'results': "Changes users can only group owner"}, status=status.HTTP_403_FORBIDDEN)

        # members_ids = set([int(member_id) for member_id in group.members.all()])

        users = User.objects.filter(
            user_groups__id=group_id
        ).annotate(
            is_performer=Exists(
                Task.objects.filter(
                    id=pk,
                    performers__id=OuterRef('id')
                )
            )
        ).order_by('-is_performer').distinct()

        serializer = UserPerformerSerializer(users, many=True)

        return Response({ 'results': serializer.data}, status=status.HTTP_200_OK)
    
    @action(methods=['post'], detail=True)
    def change_performers(self, request, pk=None, *args, **kwargs):
        task = Task.objects.prefetch_related('performers').get(id=pk)
        form_users_ids = set(request.data.get('usersIds', None))
        performers_ids = set([user.id for user in task.performers.all()])

        remove_data = performers_ids.difference(form_users_ids)
        add_data = form_users_ids.difference(performers_ids)

        if remove_data:
            task.performers.remove(*remove_data)
        
        if add_data:
            task.performers.add(*add_data)
            
        task.save()
        return Response({'results': []}, status=status.HTTP_200_OK)
    
    @action(methods=['post'], detail=False)
    def start_sessing_performer(self, request, *args, **kwargs):
        data = request.data

        user_id = request.user.id
        task_id = data.get('taskId', None)

        try:
            created = TaskPerformSession.objects.create(
                performer_id=user_id,
                task_id=task_id,
                duration=timedelta(seconds=0)
            )
        except Exception as e:
            print(e)
            return Response({ 'results': 'Error create session'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({ 'results': created}, status=status.HTTP_200_OK)
    

class TaskSessionViewSets(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes  = [IsAuthenticated]


    @action(methods=['get'], detail=True)
    def get_task_performers_sessions(self, request, pk=None, *args, **kwargs):
        data = request.GET
        is_active = data.get('is_active', None)
        user_filter = data.get('user_filter', None)
        show_unactive = data.get('unactive', None)
        page = data.get('page', None)

        if page and int(page) < 1 and type(page) != int: 
            return Response({ "results": ["page not found"]}, status=status.HTTP_404_NOT_FOUND)

        sessions_query = TaskPerformSession.objects.select_related('task', 'performer').filter(task__id=pk).order_by('-created_at')
        if is_active is not None:
            sessions_query = sessions_query.filter(is_active=True)

        if user_filter is not None:
            sessions_query = sessions_query.filter(performer__username__icontains=user_filter)

        if show_unactive is not None:
            sessions_query = sessions_query.filter(is_active=False)

        paginator = PerformerSessionsPaginator()
        result = paginator.paginate_queryset(sessions_query, request)

        if result:
            serializer = TaskPerformSessionWithUsersSerializer(result, many=True)
            return paginator.get_paginated_response(serializer.data)
            # return Response({ 'results': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({ 'results': []}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def start_session_performer(self, request, *args, **kwargs):
        data = request.data

        user_id = request.user.id
        task_id = data.get('taskId', None)

        print(task_id)

        try:
            created = TaskPerformSession.objects.create(
                performer_id=user_id,
                task_id=task_id,
                duration=timedelta(0, 0, 0, 0, 0, 0),
                is_active=True,
            )
        except Exception as e:
            print(e)
            return Response({ 'results': 'Error create session'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({ 'results': {'id': created.id}}, status=status.HTTP_200_OK)
    
    @action(methods=['patch'], detail=True)
    def update_session_performer(self, request, pk=None, *args, **kwargs):
        task_session = get_object_or_404(TaskPerformSession, id=pk)

        session_time = request.data.get('time', None)

        if not session_time:
            return Response({'results': 'Updated session error'}, status=status.HTTP_200_OK)

        if not task_session:
            return Response({'results': 'Not found task session'}, status=status.HTTP_404_NOT_FOUND)

        total_seconds = session_time // 1000
    
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        task_session.duration = timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds
        )

        task_session.save(update_fields=['duration', 'updated_at'])

        return Response({ 'results': 'Session updated!'}, status=status.HTTP_200_OK)
    
    @action(methods=['post'], detail=True)
    def end_session(self, request, pk=None, *args, **kwargs):
        task_session = get_object_or_404(TaskPerformSession, id=pk)

        time = request.data.get('time', None)

        if not task_session or not time:
            return Response({'results': ''}, status=status.HTTP_400_BAD_REQUEST)
        
        total_seconds = time // 1000
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        task_session.duration = timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds
        )
        task_session.is_active = False
        task_session.save()
        
        return Response({'results': ''}, status=status.HTTP_200_OK)
    

class TaskStatisticsViewSets(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None, *args, **kwargs):
        task = Task.objects.filter(id=pk).exists()

        if not task:
            return Response({'results': 'Not found task'}, status=status.HTTP_404_NOT_FOUND)

        task = Task.objects.prefetch_related(
            Prefetch(
                'performs_sessions',
                queryset=TaskPerformSession.objects.all().order_by('-created_at'),
                to_attr='performers_sessions'
            )
        ).get(id=pk)

        serializer = SessionSerializerWithDate(task.performers_sessions, many=True)

        return Response({'results': serializer.data}, status=status.HTTP_200_OK)


class StratagemViewSets(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Stratagem.objects.select_related('user').all()
    
    def list(self, request, *args, **kwargs):
        user = request.user
        stratagems = self.get_queryset().filter(user__id=user.id)

        serializer = StratagemShortSerializer(stratagems, many=True)

        return Response({'results': serializer.data}, status=status.HTTP_200_OK)
    

    def create(self, request, *args, **kwargs):
        data = request.data
        data['user'] = request.user.id

        serializer = StratagemCreateSerializer(data=data)

        if serializer.is_valid():
            created = serializer.save()
            serializer_obj = StratagemShortSerializer(created)
            return Response({'results': serializer_obj.data}, status=status.HTTP_200_OK)
        else:
            return Response({'results': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None, *args, **kwargs):
        print(pk)
        try:
            stratagem = Stratagem.objects.select_related('user').get(id=pk)
        except Stratagem.DoesNotExist:
            return Response({'results': 'Not found stratagem item'}, status=status.HTTP_404_NOT_FOUND)
        
        if stratagem.user.id != request.user.id:
            return Response({'results': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StratagemShortSerializer(stratagem, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'results': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'results': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        try:
            stratagem = Stratagem.objects.select_related('user').get(id=pk)
        except Stratagem.DoesNotExist:
            return Response({'results': 'Stratagem not found'}, status=status.HTTP_404_NOT_FOUND)

        if stratagem.user.id != request.user.id:
            return Response({'results': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        
        stratagem.delete()

        return Response({'results': 'Delete success'}, status=status.HTTP_204_NO_CONTENT)


API_KEY = config("CHAT_KEY", default=None)
client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(timeout=120000)
) if API_KEY else None

class ChatAiViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        schema = {
            "type": "object",
            "properties": {
                "task": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "subtasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"}
                                },
                                "required": ["title", "description"]
                            }
                        }
                    },
                    "required": ["title", "subtasks"]
                }
            },
            "required": ["task"]
        }

        INSTRUCTIONS = """
        Ты — ассистент по декомпозиции задач в таск-менеджере.
        Твоя задача: разбить описание задачи от пользователя на 3-7 конкретных подзадач.
        Каждая подзадача должна быть выполнимой за один присест, с чётким описанием действия.
        Не добавляй лишний текст, не давай советов — только структура задачи и подзадач.
        И в ответе используй язык вопроса пользователя дабы он смог понять задачу
        """


        user_input = request.data.get('input', None)

        if user_input is None:
            return Response({"results": "Not found text"},status=status.HTTP_400_BAD_REQUEST)

        if not API_KEY:
            return Response({"results": "API error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            response =async_to_sync(client.aio.models.generate_content)(
                model="gemini-3.6-flash",
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=INSTRUCTIONS,
                    response_mime_type="application/json",
                    response_schema=schema
                )
            )

            if not response.text:
                return Response({'results': "Empty text"}, status=status.HTTP_502_BAD_GATEWAY)
            else:
                import json
                return Response({"results": json.loads(response.text)}, status=status.HTTP_200_OK)
            
        except Exception as e:
            print("error", e)
            return Response({'results': f'Generation error {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

    @action(methods=['post'], detail=False)
    def created_task(self, request, *args, **kwargs):
        data = request.data

        task_data = data.get('taskData', None)
        deadline = data.get('deadLine', None)
        task_status = data.get('status', None)
        project_id = data.get('projectId', None)

        if not task_data or not deadline or not task_status or not project_id:
            return Response({'results': "insufficient data"}, status=status.HTTP_400_BAD_REQUEST)

        if not Project.objects.filter(id=project_id).exists():
            return Response({'results': "not found project"}, status=status.HTTP_404_NOT_FOUND)

        try:
            new_task = Task.objects.create(
                status=task_status,
                project_id=project_id,
                name=task_data['title'],
                description="None",
                created_by=request.user,
                deadline=deadline,
            )
        except (SyntaxError, KeyError) as error:
            new_task = None

        if new_task:
            subtasks = task_data['subtasks']
            subtasks_data = []

            for task in subtasks:
                subtasks_data.append(SubTask(
                    task=new_task,
                    title=task["title"],
                    description=task["description"],
                    priority="High",
                ))

            SubTask.objects.bulk_create(subtasks_data)


            return Response({"results": "task created"}, status=status.HTTP_200_OK)

        return Response({'results': "Error creating a task"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)