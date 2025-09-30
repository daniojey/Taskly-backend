from django.urls import path

app_name = "task"

from .views import IndexView

# urlpatterns = [
#     path('/', admin.site.urls),
# ]

urlpatterns = [
    path('', view=IndexView.as_view(), name='home_task')
]