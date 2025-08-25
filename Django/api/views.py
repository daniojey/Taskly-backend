from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.contrib.auth.mixins import LoginRequiredMixin

from task.models import Project
from users.models import Group, User
from .serializers import GroupSerializer, ProjectSerializer, UserSerializer

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
        

    def delete(self, request, pk=None, *args, **kwargs):
        if pk:
            project = Project.objects.get(pk=pk)
            project.delete()

            return Response({"message": "success delete project"}, status=status.HTTP_204_NO_CONTENT)
        
