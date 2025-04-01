from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import TimestampSigner, BadSignature
from uuid import UUID
from django.core.cache import cache

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

from common.utils import (
    validation_error_response,
    not_found_response,
    CustomPagination,
)
from .models import User
from .tokens import TokenHandler
from common.permissions import IsStaffUser
from .permissions import IsStaffOrOwner
from .tasks import send_reset_password_email
from django.db import connection, OperationalError
from django.http import JsonResponse


class HealthCheckView(APIView):
    """view for application health check"""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        """Perform a simple health check"""
        try:
            # Try running a simple query to check the database connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1;"
                )  # Simple query to ensure the database is responsive

            # Check if the necessary tables exist (optional)
            with connection.cursor() as cursor:
                # For MySQL: SHOW TABLES
                # For PostgreSQL, you can use: SELECT table_name FROM information_schema.tables WHERE table_schema='public';
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
                )
                tables = cursor.fetchall()
                if not tables:
                    return Response(
                        {
                            "message": "No tables found in the database",
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            # If the query runs successfully and tables exist, return a healthy response
            return Response(
                {"message": "Database is healthy", "total_tables": len(tables)},
                status=status.HTTP_200_OK,
            )

        except OperationalError as e:
            # If there's an error with the database connection, return a 500 response
            return Response(
                {"message": "Database connection failed", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            # Handle any other errors gracefully
            return Response(
                {"message": "An unexpected error occurred", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterView(APIView):
    """view for user Registration"""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return validation_error_response(serializer.errors)


class LoginView(APIView):
    """view for user login"""

    authentication_classes = []
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
        access_token = str(request.auth)
        TokenHandler.invalidate_access_token(access_token)
        return Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )


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
        print("get method called")
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

    def patch(self, request, id):
        """
        Allow staff users to update any user's password.
        Normal users can update their own password only.
        """
        try:
            target_user = User.objects.get(id=id, is_active=True)
            self.check_object_permissions(request, target_user)
            if (
                request.user.is_staff
                and not request.user.is_superuser
                and target_user != request.user
            ):
                return Response(
                    {"error": "you can only change the password of yours."},
                    status=status.HTTP_403_FORBIDDEN,
                )
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


def generate_custom_token(user):
    signer = TimestampSigner()
    token = default_token_generator.make_token(user)
    token_data = f"{user.id}:{token}"
    signed_token = signer.sign(token_data)
    return signed_token


def validate_custom_token(signed_token):
    signer = TimestampSigner()
    try:
        token_data = signer.unsign(
            signed_token, max_age=3600
        )  # Token expires in 1 hour
        user_id, token = token_data.split(":")
        user = User.objects.get(id=user_id)
        if default_token_generator.check_token(user, token):
            return user
    except (BadSignature, ValueError, User.DoesNotExist):
        pass
    return None


class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)

            # Check if a reset request already exists in Redis
            cache_key = f"password_reset:{user.id}"
            if cache.get(cache_key):
                return Response(
                    {
                        "error": "A reset link has already been sent. Please wait until it expires or is used."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate new reset token
            signed_token = generate_custom_token(user)
            reset_link = f"http://localhost:8000/api/auth/password-reset-confirm/{signed_token}/"  # Use HTTPS in production

            # Store the reset token in Redis (valid for 15 minutes)
            cache.set(cache_key, signed_token, timeout=300)

            # Send reset email asynchronously
            send_reset_password_email.delay(email, reset_link)

        except User.DoesNotExist:
            return Response(
                {"error": "No user found with this email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"error": "Failed to generate reset link."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Password reset email sent."}, status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, token):
        user = validate_custom_token(token)
        if not user:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            new_password = serializer.validated_data["password"]
            user.set_password(new_password)
            user.save()

            # Invalidate Redis cache entry (so user can request a new reset link if needed)
            cache_key = f"password_reset:{user.id}"
            cache.delete(cache_key)

            # Invalidate all active sessions (if using token-based authentication)
            TokenHandler.invalidate_user_tokens(user)

            return Response(
                {"message": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
