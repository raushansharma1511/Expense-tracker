from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed,PermissionDenied
import jwt
from django.utils.timezone import now
from .models import ActiveAccessToken  # Adjust the import based on your model location
from expense_tracker import settings


class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get the token from the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise PermissionDenied("Authentication credentials were not provided.")

        # Extract the token from the header
        raw_token = auth_header.split(" ")[1]

        # Check if the token exists in the database
        try:
            token_entry = ActiveAccessToken.objects.get(access_token=raw_token)
        except ActiveAccessToken.DoesNotExist:
            raise AuthenticationFailed("Invalid or unauthorized token.")

        # Decode the token and check expiration (PyJWT automatically checks for expiration)
        try:
            payload = jwt.decode(
                raw_token,
                settings.SECRET_KEY,  # Your JWT signing key
                algorithms=["HS256"],
                options={
                    "verify_exp": True
                },  # Let PyJWT automatically check the expiration
            )
        except jwt.ExpiredSignatureError:
            token_entry.delete()  # Remove expired token from the database
            raise AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token.")

        # Get the user from the token and check if the user is active
        user = token_entry.user
        if not user.is_active:
            raise AuthenticationFailed("User is inactive.")

        # Return the user and the validated token
        return (user, raw_token)
