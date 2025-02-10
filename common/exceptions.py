from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, ValidationError, AuthenticationFailed, NotFound
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler to format various exceptions globally.
    """

    # Call the default DRF exception handler
    response = exception_handler(exc, context)

    if isinstance(exc, PermissionDenied):
        # Handle PermissionDenied errors
        return Response(
            {
                "error": "Permission Denied",
                "details": str(exc),  # Optional: You can include the exception message.
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    
    elif isinstance(exc, ValidationError):
        # Handle ValidationError (usually raised by DRF serializers)
        return Response(
            {
                "error": "Validation Error",
                "details": exc.detail,  # The actual validation error details
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    elif isinstance(exc, AuthenticationFailed):
        # Handle AuthenticationFailed errors (when authentication fails)
        return Response(
            {
                "error": "Authentication Failed",
                "details": str(exc),  # Optional: You can include the exception message.
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )
    
    elif isinstance(exc, NotFound):
        # Handle NotFound errors (when a resource is not found)
        return Response(
            {
                "error": "Resource Not Found",
                "details": str(exc),
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    
    # Handle any unexpected errors (like Internal Server Errors)
    elif isinstance(exc, Exception):
        return Response(
            {
                "error": "An unexpected error occurred. Please try again later.",
                "details": str(exc),  # Optional: You can include the exception message.
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # For other errors not handled above, we return the default DRF response
    return response
