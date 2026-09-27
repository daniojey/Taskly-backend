from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from Django.main.utils.custom_api_errors import ForbiddenAPIException, TaskCreateNotValidData, TaskNotFoundId, TaskUpdateNotValidData

def custom_exception_handler(exc, context):
    if isinstance(exc, TaskCreateNotValidData):
        return Response({'detail': str(exc)}, status=TaskCreateNotValidData.status_code)
    if isinstance(exc, TaskUpdateNotValidData):
        return Response({'detail': str(exc)}, status=TaskUpdateNotValidData.status_code)
    if isinstance(exc, ForbiddenAPIException):
        return Response({"detail": str(exc)}, status=ForbiddenAPIException.status_code)
    if isinstance(exc, TaskNotFoundId):
        return Response({"detail": str(exc)}, status=TaskNotFoundId.status_code)

    return exception_handler(exc, context)