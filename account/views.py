from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, NotFound
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from uuid import UUID

from .serializers import (
    UserSerializer,
    LogInSerializer,
    LogoutSerializer,
    UserUpdateSerializer,
    UserDeleteSerializer,
    UpdatePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

# from ...expense_tracker.common.utils
from common.utils import (
    success_response,
    validation_error_response,
    not_found_response,
    permission_denied_response,
    CustomPagination,
)
from .models import ActiveAccessToken
from .models import User
from .tokens import TokenHandler
from common.permissions import IsStaffUser
from .permissions import IsStaffOrOwner
from .tasks import send_reset_password_email


class RegisterView(APIView):
    """view for user Registration"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return validation_error_response(serializer.errors)


class LoginView(APIView):
    """view for user login"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LogInSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            tokens = TokenHandler.generate_tokens_for_user(user)
            return Response(tokens, status=status.HTTP_200_OK)
        return validation_error_response(serializer.errors)


class LogoutView(APIView):
    """View for user logout"""

    def post(self, request):
        serializer = LogoutSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            access_token = str(request.auth)
            TokenHandler.invalidate_access_token(access_token)
            return Response(
                {"message": "Successfully logged out."},
                status=status.HTTP_200_OK,
            )
        return validation_error_response(serializer.errors)


class UserListView(APIView, CustomPagination):
    """View for listing all users (staff only)"""

    permission_classes = [IsStaffUser]

    def get(self, request):
        "Retrieve all the users"
        users = User.objects.all()
        paginated_users = self.paginate_queryset(users, request)
        serializer = UserSerializer(paginated_users, many=True)
        return self.get_paginated_response(serializer.data)


class UserDetailView(APIView):
    """Api view for Retrieving, updating and deleting a specific user by id.
    - Staff user can view, update and delete any user by its id.
    - Regular user can view, update and delete its own profile only.
    """

    permission_classes = [IsStaffOrOwner]

    def get_object(self, user_id):
        """Get the user object based on the ID."""
        return get_object_or_404(User, id=user_id)

    def get(self, request, id):
        """Retrieve a specific user by its id."""
        try:
            target_user = self.get_object(id)
            self.check_object_permissions(request, target_user)
        except Exception as e:
            return not_found_response("User not found.")

        serializer = UserSerializer(target_user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        """Update a specific user by its id."""
        try:
            target_user = self.get_object(id)
            self.check_object_permissions(request, target_user)
        except Exception as e:
            return not_found_response("User not found.")
        serializer = UserUpdateSerializer(
            instance=target_user,
            data=request.data,
            context={"request": request},
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return validation_error_response(serializer.errors)

    def delete(self, request, id):
        """
        Staff users can delete any user's profile by ID.
        Normal users can delete their own profile with password and refresh token.
        """
        try:
            target_user = self.get_object(id)
            self.check_object_permissions(request, target_user)
        except Exception as e:
            return not_found_response("User not found.")

        # Pass target_user to the serializer context
        serializer = UserDeleteSerializer(
            data=request.data, context={"request": request, "target_user": target_user}
        )
        if serializer.is_valid():
            serializer.delete_user(target_user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return validation_error_response(serializer.errors)


class UpdatePasswordView(APIView):
    permission_classes = [IsStaffOrOwner]

    def put(self, request, id):
        """
        Allow staff users to update any user's password.
        Normal users can update their own password only.
        """
        try:
            target_user = User.objects.get(id=id)
            self.check_object_permissions(request, target_user)
        except Exception as e:
            return not_found_response("User not found.")

        serializer = UpdatePasswordSerializer(
            data=request.data, context={"request": request, "target_user": target_user}
        )
        if serializer.is_valid():
            serializer.update_password()
            return Response(
                {"message": "Password updated successfully."}, status=status.HTTP_200_OK
            )
        return validation_error_response(serializer.errors)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(
                str(user.id).encode()
            )  # Use UUID bytes for encoding

            reset_link = (
                f"http://localhost:8000/api/auth/password-reset/confirm/{uid}/{token}/"
            )
        except Exception as e:
            return Response(
                {"error": "Failed to generate reset link."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # call the send email task
        send_reset_password_email.delay(email, reset_link)
        return Response(
            {"message": "Password reset email sent."}, status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            uid = UUID(uid)
            # Fetch the user using the decoded UID
            user = User.objects.get(id=uid)
        except (ValueError, User.DoesNotExist, TypeError):
            return not_found_response("Invalid user or token.")

        # Check the token
        if default_token_generator.check_token(user, token):
            serializer = PasswordResetConfirmSerializer(data=request.data)
            if serializer.is_valid():
                new_password = serializer.validated_data["password"]
                user.set_password(new_password)
                user.save()
                return Response(
                    {"message": "Password has been reset successfully."},
                    status=status.HTTP_200_OK,
                )
            return validation_error_response(serializer.errors)

        return Response(
            {"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST
        )
