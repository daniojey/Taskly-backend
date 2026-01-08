import mimetypes
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
from rest_framework_simplejwt.tokens import AccessToken
from django.db.models import Q, Count, Prefetch, Exists, OuterRef
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenVerifyView, TokenObtainPairView, TokenRefreshView


from main import settings
from api.utils import GroupLogger
from common.mixins import CacheMixin
from  main.settings import IS_ENABLE_CELERY
from users.models import Group, GroupLogs, Notification, User
from api.tasks import create_notify_user, create_notify_users
from task.models import Project, Task, TaskComment, TaskImage
from .serializers.group_logs_serializers import GroupLogsSerializer
from .serializers.notification_serializers import NotificationSerializer
from .serializers.task_chat_serializers import TaskChatMessageSerializer
from .serializers.task_serializers import TaskCreateSerializer, TaskSerializer
from .serializers.user_serializers import CreateUserSerializer, UserSerializer
from .serializers.group_serializers import GroupCreateSerializer, GroupSerializer
from api.paginators import ChatMessagePaginator, GroupLogsPaginator, NotificationPaginator
from .serializers.project_serializers import ProjectCreateSerializer, ProjectSerializer, ProjectWithTasksSerializer



from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def csrf(request, *args, **kwargs):
    csrf_token = get_token(request)
    response = JsonResponse({'csrfToken': 'ok'})
    response.set_cookie(
        'csrftoken',
        csrf_token,
        max_age=3600,
        secure=False,
        samesite='Lax',
    )
    return response


class CustomTokenPairView(TokenObtainPairView):

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            new_response = Response({
                'access': response.data['access'],
                'user': {
                    'id': request.user.id if hasattr(request, 'user') else None,
                    'username': request.data.get('username', None)
                }
            }, status=status.HTTP_200_OK)

            new_response.set_cookie(
                'refresh',
                response.data['refresh'],
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                samesite='Lax',
                secure=False,
            )

            return new_response
        
        return response


class CustomTokenRefreshView(TokenRefreshView):

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')

        if not refresh_token:
            return Response({
                'message': 'Token not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            if 'refresh' in response.data:
                new_refresh_token = response.data['refresh']

                response.set_cookie(
                    'refresh',
                    new_refresh_token,
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    secure=False,
                    samesite='Lax',
                    httponly=True,
                )

                del response.data['refresh']

        return response
    

    
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

        if not token:
            return Response(
                {"error": 'Token not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            access_token = AccessToken(token)
            user_id = access_token.get('user_id')

            user = User.objects.get(id=user_id)
            user_data = UserSerializer(user).data

            return Response(
                {"message": "Token is valid", "user": user_data},
                status=status.HTTP_200_OK,
            )
        
        except TokenError as e:
            raise InvalidToken(e.args[0])
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

class UserProfileAPiView(APIView):

    def get(self, request,  *args, **kwargs):
        if self.request.user.is_authenticated:
            user = User.objects.get(id=self.request.user.id)
            serializer = UserSerializer(user, context={'is_admin': self.request.user.is_superuser})

            return Response({"user": serializer.data if serializer != None else "None"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Error"}, status=status.HTTP_400_BAD_REQUEST)


class UserGroupApiView(CacheMixin, viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        filter_projects = request.GET.get('f')
        user = self.request.user
        
        match filter_projects:
            case 'A-z':
                order_by = 'name'
            case 'Z-a':
                order_by = '-name'
            case 'created':
                order_by = '-created_at'
            case _:
                order_by = 'created_at'

        queryset = request.user.user_groups.prefetch_related(
            'members',
            Prefetch(
                "projects",
                queryset=Project.objects.all().annotate(
                    task_count=Count('tasks')
                ).select_related("group").order_by('-task_count'),
                to_attr="group_projects"
            )
        ).order_by(order_by).all()

        groups = self.set_get_cache(queryset, f"groups_filter_{filter_projects}_user_{user.id}", 60)

        serializer = GroupSerializer(groups, many=True, context={"include_projects": True})

        return Response({"result": serializer.data}, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None, *args, **kwargs):
        user = request.user

        cache_data = self.get_cache(f"group_{pk}_user_{user.id}")
            
        if cache_data:
            return Response({"result": cache_data}, status=status.HTTP_200_OK)
        
        query = Group.objects.prefetch_related(
            'members',
            Prefetch(
                'projects',
                queryset=Project.objects.annotate(
                    count_tasks=Count('tasks')
                ).prefetch_related(
                    Prefetch(
                        'tasks',
                        queryset=Task.objects.all(),
                        to_attr='project_tasks'
                    )
                ).all().order_by('-count_tasks'),
                to_attr='projects_in_group'
            )
        ).get(pk=pk)
            # TODO Решить проблему неправильного создания кэша завтра
            


        if query.members.filter(id=user.id).exists():
            serializer = GroupSerializer(query, context={"include_projects": True , 'include_tasks': True, 'count_tasks': 2, 'request': request})
            self.set_cache(serializer.data, f"group_{pk}_user_{user.id}", 50)

            return Response({"result": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
    
    def create(self, request, *args, **kwargs):
        data = request.data

        serializer = GroupCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()

            return Response({"result": serializer.data}, status=status.HTTP_201_CREATED)
        
        else:
            return Response({"message": "not valid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if pk:
            group = Group.objects.get(pk=pk)
            group.delete()

            return Response({"message": "success delete group"}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def user_invite_group(self, request, pk, *args, **kwargs):
        if pk:
            try:
                data = request.data
                user_id = data.get('user_id', None)

                group = get_object_or_404(Group.objects.prefetch_related('members'), pk=pk)
                
                if not group.members.filter(id=user_id).exists():
                    
                    if IS_ENABLE_CELERY:
                        result = create_notify_user.delay(
                            user_id=user_id,
                            type_message=Notification.INVITE_MESSAGE,
                            notify_message=f"{request.user.username} wants to add you to a group",
                            push_message="You have been invited to join a group",
                            group_id=group.id
                        )
                    else :
                        create_notify_user(
                            user_id=user_id,
                            type_message=Notification.INVITE_MESSAGE,
                            notify_message=f"{request.user.username} wants to add you to a group",
                            push_message="You have been invited to join a group",
                            group_id=group.id
                        )

                    user = User.objects.only('id', 'username').get(id=user_id)

                    GroupLogger.send_invite_member(
                        group=group,
                        event_type=GroupLogs.INVITE_MEMBER,
                        target_user=user,
                        triggered_user=request.user

                    )

                    return Response({'results': 'success'}, status=status.HTTP_200_OK)
                else:
                    return Response({'errors': 'User already from this group'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                return Response({'errors': f"{e}"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'errors': 'Not found group'}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=True, methods=['post'])
    def processing_group_invite(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({'results': 'none'}, status=status.HTTP_400_BAD_REQUEST)
        
        
        data = request.data
        notify_data  = data.get('notify', None)
        notify_user = notify_data.get('user', None)

        if not notify_data and not notify_user:
            return Response({'errors': f'Not {notify_data | notify_user}'}, status=status.HTTP_400_BAD_REQUEST)

        group = get_object_or_404(
                Group.objects.prefetch_related('members').only('id', 'members'), 
                id=notify_data.get('group_id', None)
        )

        match (data.get('type', None)):
            case 'accept':
                user = get_object_or_404(User, id=notify_user.get('id', None))
                group.members.add(user)
                group.save()

                GroupLogger.add_member(
                    group=group,
                    event_type=GroupLogs.ADD_MEMBER,
                    invited_user=user,
                )

                notify = get_object_or_404(Notification, id=notify_data.get('id', None))
                notify.delete()
                return Response({'results', 'ok'}, status=status.HTTP_200_OK)
            
            case 'cancel':
                notify = get_object_or_404(Notification, id=notify_data.get('id', None))
                notify.delete()

                GroupLogger.invite_deflected(
                    group=group,
                    event_type=GroupLogs.INVITE_DEFLECTED,
                    target_user=notify_user.get('username', None)
                )
                return Response({'results': 'Invitation declined'}, status=status.HTTP_200_OK)
            
            case _:
                return Response({'errors': 'None error'}, status=status.HTTP_400_BAD_REQUEST)
            
    @action(detail=True, methods=['post'])
    def delete_member(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({'errors': 'Not id group'}, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data
        user_id = data.get('userId', None)

        if user_id:
            user = User.objects.only('id', 'username').get(id=user_id)
            group = Group.objects.get(id=pk)

            group.members.remove(user_id)
            group.save()

            GroupLogger.kick_member(
                group=group, 
                event_type=GroupLogs.KICKED_MEMBER,
                kicked_user=user,
                triggered_user=request.user
            )

            return Response({'results': 'Member Delete!'}, status=status.HTTP_200_OK)
        else:
            return Response({'results': 'Not found invited user'}, status=status.HTTP_404_NOT_FOUND)
      
            

class GroupProjectViewSet(CacheMixin,viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = get_object_or_404(Project.objects.select_related("group"), pk=self.kwargs.get('pk', None))
        return obj

    def list(self, request, *args, **kwargs):
        user = self.request.user
        queryset = request.user.user_groups.prefetch_related(
            Prefetch(
                "projects",
                queryset=Project.objects.all().select_related("group"),
                to_attr="group_projects"
            )
        ).all()

        groups = self.set_get_cache(queryset, f"groups_user_{user.id}", 70)

        serializer = GroupSerializer(groups, many=True, context={"include_projects": True})

        return Response({"result": serializer.data}, status=status.HTTP_200_OK)


    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = ProjectCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()

            return Response({'message': serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'error', "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = Project.objects.select_related(
                'group'
            ).prefetch_related(
                Prefetch(
                    'tasks',
                    queryset=Task.objects.all(),
                    to_attr='project_tasks'
                )
            ).get(pk=pk)

            if not obj:
                return Response({'message': '404'}, status=status.HTTP_404_NOT_FOUND)
            
            if obj.group and obj.group.id in request.user.user_groups.all():
                return Response({'message': "403"}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = ProjectWithTasksSerializer(obj)

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

class TaskViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]


    def get_queryset(self):
        project_id = self.kwargs.get('project_id', None)

        if project_id:
            tasks = Task.objects.select_related("owner", 'project').filter(project__id=project_id)
        else:
            tasks  = Task.objects.select_related("owner", 'project').all()
        return tasks
    
    def get_project(self):
        project_id = self.kwargs.get('project_id', None)

        project = get_object_or_404(Project.objects.select_related('group'), id=project_id)

        return project
    
    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=self.kwargs.get('pk'))
        return obj
    
    def create(self, request, *args, **kwargs):
        project = self.get_project()

        data = request.data
        data['project'] = project.id
        data['created_by'] = request.user.id if hasattr(request, 'user') else None
        serializer = TaskCreateSerializer(data=data)


        if serializer.is_valid():
            serializer.save()
            
            return Response({'result': serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.owner.id != request.user.id:
            return Response({'message': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(
            instance,
            data=request.data,
            partial=True,
            context={'method': 'path'}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message":"Task partially updated!", 'result': serializer.data},
                status=status.HTTP_200_OK
            )
        
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        serializer = TaskSerializer(queryset, many=True, context={"method": "get"})

        return Response({'result': serializer.data, 'project': kwargs.get('project_id', None)}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None, *args, **kwargs):
        user = request.user

        task = Task.objects.get(pk=pk)

        data = request.data

        new_status = data.get('new_status', None)

        if new_status and task.status != new_status:
            task.status = new_status
            task.save()


        if IS_ENABLE_CELERY:
            create_notify_users.delay(group=task.group, task_name=task.name, task_status=task.status)
        else:
            create_notify_users(group=task.group, task_name=task.name, task_status=task.status)
        # chanel_layer = get_channel_layer()
        # async_to_sync(chanel_layer.group_send)(f"base_group_{user.id}", {'type': 'chat_message', 'message': 'lobzik', 'datas': 'data1', 'task_id': task.id})

        return Response({'result': task.status}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk:
            try:
                task = Task.objects.get(pk=pk)
            except Task.DoesNotExist:
                return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = TaskSerializer(task, context={"method": 'get'})

            return Response({'result': serializer.data}, status=status.HTTP_200_OK)
        

    def delete(self, request, pk=None, *args, **kwargs):
        if pk:
            try:
                task = Task.objects.select_related("owner").get(pk=pk)
            except Task.DoesNotExist:
                return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if task.owner.id == request.user.id:
                task.delete()
            else:
                return Response({'message': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

            return Response({'message':'success delete'}, status=status.HTTP_204_NO_CONTENT)


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
            serializer = GroupLogsSerializer(logs, many=True)
            return paginator.get_paginated_response(serializer.data)

        else:
            return Response({'results': []}, status=status.HTTP_200_OK)
        # return Response({'results': serializer.data}, status=status.HTTP_200_OK)

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