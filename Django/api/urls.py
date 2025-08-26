from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import TaskViewSet, UserProfileAPiView, UserGroupApiView, GroupProjectViewSet

app_name = "api"

router = DefaultRouter()

router.register("groups", UserGroupApiView, basename="groups")
router.register("groups-projects", GroupProjectViewSet, basename="groups-projects")
router.register(r'projects/(?P<project_id>\d+)/tasks', TaskViewSet, basename='task')


urlpatterns = [
    path("", view=UserProfileAPiView.as_view(), name="profile"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns += router.urls