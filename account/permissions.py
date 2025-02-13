from rest_framework.permissions import BasePermission


class IsStaffOrOwner(BasePermission):
    """
    Custom permission to:
    - Allow staff users to view all users but only manage non-deleted ones.
    - Allow normal users to view, update, and delete only their own non-deleted profile.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method == "GET":
            if request.user.is_staff:
                return True
            else:
                if obj.is_active and obj == request.user:
                    return True
            return False

        return obj.is_active and (request.user.is_staff or obj == request.user)
