from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
    AuthenticationFailed,
    NotFound,
)
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler to format various exceptions globally.
    """

    response = exception_handler(exc, context)
    print(type(response))

    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "error": "Permission Denied",
                "details": str(exc),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    elif isinstance(exc, ValidationError):
        return Response(
            {
                "error": "Validation Error",
                "details": exc.detail,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    elif isinstance(exc, AuthenticationFailed):

        return Response(
            {
                "error": "Authentication Failed",
                "details": str(exc),
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    elif isinstance(exc, NotFound):

        return Response(
            {
                "error": "Resource Not Found",
                "details": str(exc),
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    elif isinstance(exc, Exception):
        return Response(
            {
                "error": "An unexpected error occurred. Please try again later.",
                "details": str(exc),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
