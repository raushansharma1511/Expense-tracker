import logging
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.exceptions import ValidationError
from .models import ActiveAccessToken

# Set up logging
logger = logging.getLogger(__name__)


class TokenHandler:
    """
    Utility class to handle token-related operations.
    """

    @staticmethod
    def invalidate_user_session(user, access_token):
        """
        Invalidate the user's session by removing the active access token and
        optionally blacklisting the refresh token if provided.
        """
        if access_token:
            TokenHandler.invalidate_access_token(access_token)
        TokenHandler.invalidate_user_tokens(user)
        logger.info(f"User session invalidated for {user.username}.")

    @staticmethod
    def generate_tokens_for_user(user):
        """
        Generate access and refresh tokens for a user.
        """
        access_token = str(AccessToken.for_user(user))
        refresh_token = str(RefreshToken.for_user(user))

        # Store the active access token in the database
        ActiveAccessToken.objects.create(user=user, access_token=access_token)
        logger.info(f"Generated tokens for user {user.username}.")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def invalidate_user_tokens(user):
        """
        Invalidate all active tokens for a given user.
        """
        deleted_count, _ = ActiveAccessToken.objects.filter(user=user).delete()
        logger.info(f"Invalidated {deleted_count} tokens for user {user.username}.")

    @staticmethod
    def invalidate_access_token(token):
        """
        Invalidate a specific access token.
        """
        deleted_count, _ = ActiveAccessToken.objects.filter(access_token=token).delete()
        if deleted_count == 0:
            logger.warning(f"Attempted to invalidate a non-existent token: {token}.")
        else:
            logger.info(f"Invalidated access token: {token}.")

    @staticmethod
    def blacklist_refresh_token(refresh_token):
        """
        Blacklist a given refresh token.
        """
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"Blacklisted refresh token: {refresh_token}.")
        except Exception as e:
            logger.error(f"Error blacklisting refresh token {refresh_token}: {str(e)}")
            raise ValidationError(f"Error blacklisting refresh token: {str(e)}")
