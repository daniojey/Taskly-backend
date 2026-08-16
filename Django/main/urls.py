from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.views.static import serve

from main import settings
import api

urlpatterns = [
    path('admin/', admin.site.urls),

    re_path(r'^api/(?P<version>(v1|v2))/', include("api.urls", namespace='api')),
    path('api/v1/drf-auth/', include('rest_framework.urls')),
    path('tasks/', include('task.urls', namespace='task')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns  +=  [ path ( 'silk/' ,  include ( 'silk.urls' ,  namespace = 'silk' ))]
