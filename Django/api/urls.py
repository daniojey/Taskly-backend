from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UserProfileAPiView, UserGroupApiView

app_name = "api"

router = DefaultRouter()

router.register("groups", UserGroupApiView, basename="groups")


urlpatterns = [
    path("", view=UserProfileAPiView.as_view(), name="profile"),
]

urlpatterns += router.urls