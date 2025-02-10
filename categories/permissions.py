from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied


class CanManageCategories(BasePermission):
    """
    Custom permission to:
    - Allow staff users to view all categories but only manage non-deleted ones.
    - Allow normal users to view, update, and delete only their own non-deleted categories.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Staff can view all categories
        if request.method == "GET":
            if request.user.is_staff:
                return True
            else:
                if not obj.is_deleted and (
                    obj.is_predefined or obj.user == request.user
                ):
                    return True
            return False

        else:
            if not obj.is_deleted:
                if request.user.is_staff:
                    return True
                else:
                    return obj.user == request.user
        return False
