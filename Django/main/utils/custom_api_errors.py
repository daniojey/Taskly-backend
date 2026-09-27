from rest_framework.exceptions import APIException

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