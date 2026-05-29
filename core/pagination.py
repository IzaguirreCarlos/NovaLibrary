"""Custom pagination classes for Lexora Library API."""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from typing import Any


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination with metadata envelope."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data: list) -> Response:
        return Response({
            "status": "success",
            "pagination": {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page_size": self.get_page_size(self.request),
            },
            "results": data,
        })

    def get_paginated_response_schema(self, schema: dict) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "pagination": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "total_pages": {"type": "integer"},
                        "current_page": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "page_size": {"type": "integer"},
                    },
                },
                "results": schema,
            },
        }


class LargeResultsSetPagination(PageNumberPagination):
    """Large pagination for admin views."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
