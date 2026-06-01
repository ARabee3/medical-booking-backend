"""
Custom exception handler.

Formats DRF validation errors to match the frontend ApiError type:
    { "detail": "..." }  or  { "field": ["error message"] }
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns a consistent error shape.

    - 404 errors: {"detail": "Not found."}
    - 403 errors: {"detail": "You do not have permission to perform this action."}
    - 400 validation errors: {"field": ["error"], ...}
    """
    response = exception_handler(exc, context)

    if response is not None:
        # If it's a validation error with field errors, keep the default shape
        if isinstance(response.data, dict) and any(
            isinstance(v, list) for v in response.data.values()
        ):
            return response

        # For other errors, wrap in a detail key if not already
        if "detail" not in response.data and len(response.data) == 1:
            first_key = list(response.data.keys())[0]
            response.data = {"detail": response.data[first_key]}

    return response
