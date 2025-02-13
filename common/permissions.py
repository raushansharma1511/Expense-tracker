from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class IsStaffUser(BasePermission):
    """
    Custom permission to allow only staff users to access the view.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated) and request.user.is_staff


class IsStaffOrOwner(BasePermission):
    """
    Custom permission to:
    - Allow staff users to view all objects but only manage non-deleted ones.
    - Allow normal users to view, update, and delete only their own non-deleted objects.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method == "GET":
            if request.user.is_staff:
                return True
            else:
                if not obj.is_deleted and obj.user == request.user:
                    return True
            return False

        return obj.is_deleted == False and (
            request.user.is_staff or obj.user == request.user
        )
