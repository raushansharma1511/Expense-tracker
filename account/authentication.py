from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import UntypedToken
from jwt import decode as jwt_decode
from .models import ActiveAccessToken
from datetime import datetime, timezone
from django.conf import settings


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        # Ensure the header starts with "Bearer"
        if not auth_header.startswith("Bearer "):
            return None

        # Extract the token part after "Bearer"
        raw_token = auth_header.split(" ")[1]

        # Check if the token exists in the database
        try:
            token_entry = ActiveAccessToken.objects.get(access_token=raw_token)
        except ActiveAccessToken.DoesNotExist:
            raise AuthenticationFailed("Invalid or unauthorized token.")

        # Validate the expiration time from the token
        try:

            payload = jwt_decode(
                raw_token,
                settings.SECRET_KEY,  # Replace with your JWT signing key
                algorithms=["HS256"],
                options={"verify_exp": False},
            )

            # Get expiration time from the payload
            expiration = payload.get("exp")

            if expiration:
                current_time = datetime.now(timezone.utc)
                exp_time = datetime.fromtimestamp(expiration, tz=timezone.utc)

                if exp_time < current_time:
                    token_entry.delete()  # removes expired token from database
                    raise AuthenticationFailed("Token has expired.")

        except Exception as e:
            raise AuthenticationFailed("Invalid or expired token.")

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
