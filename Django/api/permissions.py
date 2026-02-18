
from rest_framework.permissions import BasePermission, SAFE_METHODS


class OwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Для безопасных методов — всем можно
        if request.method in SAFE_METHODS:
            return True
        # Для остальных — только аутентифицированным
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        
        return bool(obj.owner == request.user)