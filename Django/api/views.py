from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.contrib.auth.mixins import LoginRequiredMixin

from task.models import Project, Task
from users.models import Group, User
from .serializers import GroupSerializer, ProjectSerializer, TaskSerializer, UserSerializer

class UserProfileAPiView(APIView):

    def get(self, request,  *args, **kwargs):
        if self.request.user.is_authenticated:
            user = User.objects.get(id=self.request.user.id)
            serializer = UserSerializer(user, context={'is_admin': self.request.user.is_superuser})

            return Response({"user": serializer.data if serializer != None else "None"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Error"}, status=status.HTTP_400_BAD_REQUEST)


class UserGroupApiView(LoginRequiredMixin, viewsets.ViewSet):
    
    def list(self, request, *args, **kwargs):
        queryset = self.request.user.user_groups.all()

        serializer = GroupSerializer(queryset, many=True)

        return Response({"result": serializer.data}, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None, *args, **kwargs):
        if pk:
            user = request.user
            group = Group.objects.get(pk=pk)

            if user.id in group.members.all().values_list("id", flat=True):
                serializer = GroupSerializer(group)

                return Response({"result": serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
    
    def create(self, request, *args, **kwargs):
        data = request.data

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
        


class GroupProjectViewSet(LoginRequiredMixin, viewsets.ViewSet):

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

        print(queryset)

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
        

class TaskViewSet(LoginRequiredMixin, viewsets.ViewSet):


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
