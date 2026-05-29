"""Review API ViewSet."""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.reviews.models import Review
from apps.api.serializers import ReviewSerializer, ReviewCreateSerializer
from permissions.api_permissions import IsLibrarian, IsOwnerOrReadOnly


@extend_schema(tags=["reviews"])
class ReviewViewSet(viewsets.ModelViewSet):
    """
    Book reviews and ratings.

    - GET /reviews/?book=<id> — book reviews
    - POST /reviews/ — create review (one per user per book)
    - PATCH /reviews/{id}/ — update (owner only)
    - DELETE /reviews/{id}/ — delete (owner or librarian)
    """
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "rating"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_queryset(self):
        qs = Review.objects.filter(is_approved=True).select_related("user", "book")
        book_id = self.request.query_params.get("book")
        if book_id:
            qs = qs.filter(book_id=book_id)
        return qs

    @extend_schema(summary="Aprobar reseña (solo bibliotecarios)")
    @action(detail=True, methods=["post"], permission_classes=[IsLibrarian])
    def approve(self, request, pk=None):
        review = self.get_object()
        review.is_approved = True
        review.save(update_fields=["is_approved"])
        return Response({"status": "success", "message": "Reseña aprobada."})

    @extend_schema(summary="Marcar reseña como útil")
    @action(detail=True, methods=["post"])
    def helpful(self, request, pk=None):
        review = self.get_object()
        review.helpful_count += 1
        review.save(update_fields=["helpful_count"])
        return Response({"status": "success", "helpful_count": review.helpful_count})
