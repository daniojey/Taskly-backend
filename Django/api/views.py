from django.db.models import Prefetch
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenVerifyView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken, AccessToken
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.decorators import action

from task.models import Project, Task
from users.models import Group, User
from .serializers import GroupSerializer, ProjectSerializer, TaskSerializer, UserSerializer
from api import serializers



from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def csrf(request, *args, **kwargs):
    csrf_token = get_token(request)
    # Возвращаем токен в JSON и устанавливаем куки
    response = JsonResponse({'csrfToken': 'ok'})
    response.set_cookie(
        'csrftoken',
        csrf_token,
        max_age=3600,
        secure=False,  # True в production с HTTPS
        samesite='Lax',
    )
    return response

# class GetCSRFToken(APIView):
#     def get(self, request, *args, **kwargs):
#         token = get_token(request)
#         return Response({'csrfToken': token})
    
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
            user_data = serializers.UserSerializer(user).data

            return Response(
                {"message": "Token is valid", "user": user_data},
                status=status.HTTP_200_OK,
            )
        
        except TokenError as e:
            print("ОШИБКА ТОКЕНА")
            raise InvalidToken(e.args[0])
        except User.DoesNotExist:
            print("ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН")
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


class UserGroupApiView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        filter_projects = request.GET.get('f')
        
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
            Prefetch(
                "projects",
                queryset=Project.objects.all().select_related("group"),
                to_attr="group_projects"
            )
        ).order_by(order_by).all()

        # print("QUERYSET",queryset.group_projects)
        # for g in queryset:
        #     print(g.group_projects)

        serializer = GroupSerializer(queryset, many=True, context={"include_projects": True})

        return Response({"result": serializer.data}, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk:
            user = request.user
            group = Group.objects.get(pk=pk)

            if user.id in group.members.all().values_list("id", flat=True):
                serializer = GroupSerializer(group, context={"include_projects": True , 'include_tasks': True, 'count_tasks': 2, 'request': request})

                return Response({"result": serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
    
    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)

        serializer = GroupSerializer(data=data)

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
        


class GroupProjectViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = get_object_or_404(Project.objects.select_related("group"), pk=self.kwargs.get('pk', None))
        return obj

    def list(self, request, *args, **kwargs):
        queryset = request.user.user_groups.prefetch_related(
            Prefetch(
                "projects",
                queryset=Project.objects.all().select_related("group"),
                to_attr="group_projects"
            )
        ).all()

        print("QUERYSET",queryset)

        serializer = GroupSerializer(queryset, many=True, context={"include_projects": True})

        return Response({"result": serializer.data}, status=status.HTTP_200_OK)


    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = ProjectSerializer(data=data)

        if serializer.is_valid():
            serializer.save()

            return Response({'message': serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'error', "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = Project.objects.get(pk=pk)

            if not obj:
                return Response({'message': '404'}, status=status.HTTP_404_NOT_FOUND)
            
            if obj.group and obj.group.id in request.user.user_groups.all():
                return Response({'message': "403"}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = ProjectSerializer(obj)

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
            project = Project.objects.get(pk=pk)
            project.delete()

            return Response({"message": "success delete project"}, status=status.HTTP_204_NO_CONTENT)
        

class TaskViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


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
        data['owner'] = request.user.id
        data['group'] = project.group.id
        serializer = TaskSerializer(data=data)

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
        print(pk)

        task = Task.objects.get(pk=pk)
        print(task)
        print(task.status)

        data = request.data

        new_status = data.get('new_status', None)

        if new_status and task.status != new_status:
            task.status = new_status
            task.save()

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
