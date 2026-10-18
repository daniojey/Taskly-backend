from rest_framework.exceptions import APIException


# AUTH
class UncorrectToken(APIException):
    status_code = 400
    default_detail = "Not valid token"
    default_code = "error"

class NotFoundToken(APIException):
    status_code = 404
    default_detail = "Not found token"
    default_code = "error"

class NotFoundRefreshToken(APIException):
    status_code = 404
    default_detail = "Not found refresh token"
    default_code = "error"

# Group
class GroupNotFound(APIException):
    status_code = 404
    default_detail = "Group not found"
    default_code = "error"

class GroupForbidden(APIException):
    status_code = 403
    default_detail = "Group forbidden"
    default_code = "error"

class UserAlreadyExistInGroup(APIException):
    status_code = 400
    default_detail = "This user already exist in this group"
    default_code = "error"


# User
class UserNotFound(APIException):
    status_code = 404
    default_detail = "User not found"
    default_code = "error"

# TaskView
class ForbiddenAPIException(APIException):
    status_code = 403
    default_detail = "You do not have access to this information"
    default_code = "forbidden"

class TaskCreateNotValidData(APIException):
    status_code = 400
    default_detail = "Data not valid"
    default_code = "error"


class TaskUpdateNotValidData(APIException):
    status_code = 400
    default_detail = "Data not valid"
    default_code = "error"

class TaskNotFoundId(APIException):
    status_code = 404
    default_detail = "Not found task id"
    default_code = "error"


# Notification
class NotFoundNotifyData(APIException):
    status_code = 404
    default_detail = "Not found user data"
    default_code = "error"


# Other
class NotFoundValueInData(APIException):
    status_code = 400
    default_detail = "Not found variable in data"
    default_code = "error"