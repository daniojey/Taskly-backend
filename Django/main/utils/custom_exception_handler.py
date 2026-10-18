from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from main.utils.custom_api_errors import (
    # Auth
    GroupForbidden,
    GroupNotFound,
    NotFoundNotifyData,
    NotFoundValueInData,
    UncorrectToken,
    NotFoundToken,
    NotFoundRefreshToken,
    UserAlreadyExistInGroup,

    #User
    UserNotFound,

    # TaskView
    ForbiddenAPIException, 
    TaskCreateNotValidData, 
    TaskNotFoundId, 
    TaskUpdateNotValidData
)

def custom_exception_handler(exc, context):
    # AUTH
    if isinstance(exc, UncorrectToken):
        return Response({'detail': str(exc)}, status=UncorrectToken.status_code)
    if isinstance(exc, NotFoundToken):
        return Response({'detail': str(exc)}, status=NotFoundToken.status_code)
    if isinstance(exc, NotFoundRefreshToken):
        return Response({'detail': str(exc)}, status=NotFoundRefreshToken.status_code)

    # TaskViewSet
    if isinstance(exc, TaskCreateNotValidData):
        return Response({'detail': str(exc)}, status=TaskCreateNotValidData.status_code)
    if isinstance(exc, TaskUpdateNotValidData):
        return Response({'detail': str(exc)}, status=TaskUpdateNotValidData.status_code)
    if isinstance(exc, ForbiddenAPIException):
        return Response({"detail": str(exc)}, status=ForbiddenAPIException.status_code)
    if isinstance(exc, TaskNotFoundId):
        return Response({"detail": str(exc)}, status=TaskNotFoundId.status_code)

    # Group
    if isinstance(exc, GroupNotFound):
        return Response({'detail': str(exc)}, status=GroupNotFound.status_code)
    if isinstance(exc, GroupForbidden):
        return Response({'detail': str(exc)}, status=GroupForbidden.status_code)
    if isinstance(exc, UserAlreadyExistInGroup):
        return Response({'detail': str(exc)}, status=UserAlreadyExistInGroup.status_code)

    # User
    if isinstance(exc, UserNotFound):
        return Response({'detail': str(exc)}, status=UserNotFound.status_code)

    # Notification
    if isinstance(exc, NotFoundNotifyData):
        return Response({'detail': str(exc)}, status=NotFoundNotifyData.status_code)

    # Other
    if isinstance(exc, NotFoundValueInData):
        return Response({'detail': str(exc)}, status=NotFoundValueInData.status_code)

    
    return exception_handler(exc, context)