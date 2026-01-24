"""
Custom exception handlers for REST framework.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns structured error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            # Multiple field errors
            errors = exc.message_dict
        elif hasattr(exc, "messages"):
            # List of error messages
            errors = {"detail": exc.messages}
        else:
            # Single error message
            errors = {"detail": str(exc)}

        response = Response(errors, status=status.HTTP_400_BAD_REQUEST)

    # Add custom error formatting if response exists
    if response is not None:
        # Ensure consistent error format
        if isinstance(response.data, dict):
            if "detail" not in response.data and "error" not in response.data:
                # If it's field errors, keep them as is
                pass
            else:
                # Standardize single error messages
                if "detail" in response.data:
                    response.data = {"error": response.data["detail"]}
        elif isinstance(response.data, list):
            response.data = {"errors": response.data}

    return response
