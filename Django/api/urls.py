from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UserProfileAPiView, UserGroupApiView, GroupProjectViewSet

app_name = "api"

router = DefaultRouter()

router.register("groups", UserGroupApiView, basename="groups")
router.register("groups-projects", GroupProjectViewSet, basename="groups-projects")


urlpatterns = [
    path("", view=UserProfileAPiView.as_view(), name="profile"),
]

urlpatterns += router.urls