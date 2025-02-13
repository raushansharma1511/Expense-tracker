from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, ValidationError


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page": self.page.number,
                "total_pages": self.page.paginator.num_pages,
                "items": data,
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
        uuid_obj = uuid.UUID(value)
        return True
    except ValueError:
        return False
