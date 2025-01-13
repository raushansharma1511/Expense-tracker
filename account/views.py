# users/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed

from .serializers import UserSerializer, LogInSerializer
from .models import ActiveAccessToken

from .models import User
from django.contrib.auth.hashers import make_password


class UserRegistrationView(APIView):
    """view for user Registration"""

    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.save()
            return Response(
                {"message": "User created successfully!", "user": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """view for user login"""

    def post(self, request):

        serializer = LogInSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data

            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # save the access token in db
            ActiveAccessToken.objects.create(access_token=str(access_token), user=user)
            return Response(
                {
                    "message": "login successfull",
                    "access_token": str(access_token),
                    "refresh_token": str(refresh),
                },
                status=200,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """view for user logout"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get the refresh token from the request data
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token = str(request.auth)

            if access_token:
                try:
                    token_object = ActiveAccessToken.objects.filter(
                        access_token=access_token
                    )
                except ActiveAccessToken.DoesNotExist:
                    raise AuthenticationFailed("Invalid or unauthorized token.")

                token_object.delete()

            else:
                raise AuthenticationFailed("Access token required.")

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Successfully logged out."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:

            return Response(
                {"error": "Invalid refresh token or already blacklisted."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UpdatePasswordView(APIView):
    "View to update the password of a user"
    permission_classes = [IsAuthenticated]

    def put(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        user: User = request.user

        if not user.check_password(old_password):
            return Response(
                {"error": "please provide the valid old password"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if old_password == new_password:
            return Response(
                {
                    "error": "old and new password is same provide different new password that old one."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        ActiveAccessToken.objects.filter(user=user).delete()
        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "password updated successfully"},
            status=status.HTTP_200_OK,
        )


class UserDetailView(APIView):
    """ "view to retrieve and update user account"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve the account details of the current logined user"""
        user = request.user  # Get the authenticated user
        serializer = UserSerializer(user)
        return Response(
            {"user": serializer.data},
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        """Update the account details of the current logined user"""

        if request.data.get("password"):
            return Response(
                {
                    "error": "password can't be updated in this request so don't provide password."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.data.get("is_staff"):
            return Response(
                {
                    "error": "You cannot change the staff status of your account by itself."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSerializer(
            instance=request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Profile updated successfully.", "user": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteUserView(APIView):
    """ "Api view to deactivate user profile"""

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """Deactivate the account of the current logined user"""
        user = request.user

        user.is_active = False  # soft delete
        user.save()

        if user.is_staff:
            # Set user field to None for categories created by this staff member
            user.categories.update(user=None)

        # also logout its active session by deleting all its active token stored in db
        active_tokens = ActiveAccessToken.objects.filter(user=request.user)
        for token in active_tokens:
            token.delete()

        return Response(
            {"message": f"User '{user.username}' has been deactivated."},
            status=status.HTTP_200_OK,
        )
