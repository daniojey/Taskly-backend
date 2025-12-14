from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from .views import (
    DownloadChatImagesView,
    ChatMessagesListView,
    CustomTokenVerifyView,
    GroupLogsViewSet,
    NotificationViewSet,
    TaskViewSet, 
    UserProfileAPiView, 
    UserGroupApiView, 
    GroupProjectViewSet,
    UserViewSet,
    csrf
)

app_name = "api"

router = DefaultRouter()

router.register("groups", UserGroupApiView, basename="groups")
router.register(r'group/(?P<group_id>\d+)/logs', GroupLogsViewSet, basename='group-logs')
router.register("groups-projects", GroupProjectViewSet, basename="groups-projects")
router.register(r'projects/(?P<project_id>\d+)/tasks', TaskViewSet, basename='task')
router.register('tasks', TaskViewSet, basename='tasks')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('users', UserViewSet, basename='users')
# router.register('chat-messages', ChatMessagesListView, basename='chat-messages')


urlpatterns = [
    path('csrf/', csrf, name="get_csrf"),
    path("", view=UserProfileAPiView.as_view(), name="profile"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('chat-messages/<int:task_id>/', ChatMessagesListView.as_view(), name='chat-messages'),
    path('download/<int:message_id>/', DownloadChatImagesView.as_view(), name='download_image'),
]

urlpatterns += router.urls