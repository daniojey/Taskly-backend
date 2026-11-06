from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsStratagemOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        return bool(obj.user_id == request.user.id)