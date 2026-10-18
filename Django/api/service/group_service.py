from django.db.models import BooleanField, Case, Count, Prefetch, Value, When
from django.shortcuts import get_object_or_404
from rest_framework import status

from api.utils import GroupLogger
from api.tasks import create_notify_user
from main.settings import IS_ENABLE_CELERY
from common.cache_managers.group_cache import GroupCacheManager
from common.mixins import CacheMixin
from main.utils.custom_api_errors import GroupForbidden, GroupNotFound, NotFoundValueInData, UserAlreadyExistInGroup, UserNotFound
from api.serializers.group_serializers import GroupCountProjectsSerializer, GroupCreateSerializer, GroupDetailSerializer
from task.models import Project, Task
from users.models import Group, GroupLogs, Notification, User

from rest_framework.response import Response

class GroupService:

    @staticmethod
    def get_list_queryset(request, filter_projects, user, cache_mixin: CacheMixin):

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
                'projects',
                    queryset=Project.objects.all(),
                    to_attr='count_projects'
                ),
        
            Prefetch(
                'members',
                    queryset=User.objects.all(),
                    to_attr='count_members'
                )
            ).order_by(order_by).all()
        
        groups = cache_mixin(queryset, f"groups_filter_{filter_projects}_user_{user.id}", 60)
        
        serializer = GroupCountProjectsSerializer(groups, many=True, context={"include_projects": True})
        
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)

    @staticmethod
    def get_group(request, user, set_cache, group_id):
        try:
            query = Group.objects.prefetch_related(
                Prefetch(
                    'members',
                    queryset=User.objects.all(),
                    to_attr='prefetch_members'
                ),
                Prefetch(
                    'projects',
                    queryset=Project.objects.annotate(
                    count_tasks=Count('tasks')
                ).prefetch_related(
                    Prefetch(
                        'tasks',
                        queryset=Task.objects.all()[:2],
                        to_attr='project_tasks'
                    )
                ).all().order_by('-count_tasks'),
                to_attr='projects_in_group'
            )
            ).annotate(
                is_owner=Case(
                When(owner=request.user, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
            ).only('id', 'name').get(pk=group_id)
        
            if query.members.filter(id=user.id).exists():
                serializer = GroupDetailSerializer(query, context={'request': request})
                set_cache(serializer.data, f"group_{group_id}_user_{user.id}", 50)
        
                return Response({"results": serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
        except Group.DoesNotExist:
            raise GroupNotFound

    @staticmethod
    def group_create(request, group_data):

        group_limit = Group.objects.filter(owner__id=request.user.id).count()

        if group_limit >= 8:
            return Response({'results': 'The limit for creating groups has been reached'}, status=status.HTTP_403_FORBIDDEN)

        serializer = GroupCreateSerializer(data=group_data)

        if serializer.is_valid():
            serializer.save()


            GroupCacheManager.clean_group_list_cache(
                filters=['A-z', 'Z-a', 'created', ''],
                user_id=request.user.id
            )

            return Response({"result": serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({"result": "not valid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    @staticmethod
    def group_delete(group, request):
        if not group:
            raise GroupNotFound

        if group.owner.id == request.user.id:
            group.delete()
        else:
            raise GroupForbidden

        return Response({"message": "success delete group"}, status=status.HTTP_204_NO_CONTENT)


    @staticmethod
    def user_invite_group(data, request, pk):
        user_id = data.get('user_id', None)
        
        group = get_object_or_404(Group.objects.prefetch_related('members'), pk=pk)

        if not group:
            raise GroupNotFound

        if not group.members.filter(id=user_id).exists():

            if IS_ENABLE_CELERY:
                create_notify_user.delay(
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
            raise UserAlreadyExistInGroup

    @staticmethod
    def processing_group_invite(request, pk):
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
                raise NotFoundValueInData


    @staticmethod
    def delete_member(request, pk, check_permissions):
        data = request.data
        user_id = data.get('userId', None)

        if not user_id:
            raise UserNotFound
        
        try:
            user = User.objects.only('id', 'username').get(id=user_id)
            group = Group.objects.select_related('owner').get(id=pk)
        
            check_permissions(request, group)
        
            group.members.remove(user_id)
            group.save()
        
            GroupLogger.kick_member(
                group=group, 
                event_type=GroupLogs.KICKED_MEMBER,
                kicked_user=user,
                triggered_user=request.user
            )
        
            return Response({'results': 'Member Delete!'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            raise UserNotFound
        except Group.DoesNotExist:
            raise GroupNotFound