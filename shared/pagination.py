"""
Shared pagination class.

Provides consistent pagination across all list endpoints.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination: 20 items per page by default."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
