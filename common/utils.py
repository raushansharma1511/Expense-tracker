from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, ValidationError


class CustomPagination(PageNumberPagination):
    page_size = 10  # Default number of items per page
    page_size_query_param = "page_size"  # Allow client to set page size
    max_page_size = 100  # Maximum page size allowed

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,  # Total number of items
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page": self.page.number,  # Current page number
                "total_pages": self.page.paginator.num_pages,  # Total pages
                "items": data,  # Paginated data
            }
        )


def not_found_response(message, status_code=status.HTTP_404_NOT_FOUND):
    """Create a standard response structure for success or error."""
    response_data = {
        "error": message,
    }
    return Response(response_data, status=status_code)


def permission_denied_response(message, status_code=status.HTTP_403_FORBIDDEN):
    """Create a standard response structure for success or error."""
    response_data = {
        "message": message,
    }
    return Response(response_data, status=status_code)


def validation_error_response(errors):
    error = {}
    for field_name, field_errors in errors.items():
        error[field_name] = field_errors[0]

    return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)



import uuid

def is_valid_uuid(value):
    try:
        # Try to create a UUID object from the given string.
        uuid_obj = uuid.UUID(value)
        return True  # If no error, it's a valid UUID.
    except ValueError:
        # If ValueError is raised, the string is not a valid UUID.
        return False