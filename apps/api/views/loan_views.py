"""API ViewSet for loans."""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.loans.models import Loan
from apps.books.models import Book
from apps.api.serializers import LoanSerializer, LoanCreateSerializer
from permissions.api_permissions import IsLibrarian, IsOwnerOrLibrarian
from services.loan_service import LoanService
from core.exceptions import (
    BookNotAvailableError, LoanLimitExceededError,
    UserHasOverdueLoanError, LoanAlreadyReturnedError, RenewalLimitExceededError,
)
from repositories.loan_repository import LoanRepository


@extend_schema(tags=["loans"])
class LoanViewSet(viewsets.ModelViewSet):
    """
    Loan management endpoints.

    - GET /loans/ — my active loans (member) / all loans (librarian)
    - POST /loans/ — create loan
    - GET /loans/{id}/ — loan detail
    - POST /loans/{id}/return/ — return book
    - POST /loans/{id}/renew/ — renew loan
    - GET /loans/overdue/ — all overdue loans (librarian only)
    - GET /loans/history/ — full loan history for current user
    """
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["loan_date", "due_date", "status"]
    ordering = ["-loan_date"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.is_librarian:
            return Loan.objects.all().select_related("user", "book").prefetch_related("book__authors")
        return LoanRepository.get_all_by_user(user)

    def get_serializer_class(self):
        if self.action == "create":
            return LoanCreateSerializer
        return LoanSerializer

    @extend_schema(summary="Solicitar préstamo")
    def create(self, request, *args, **kwargs):
        serializer = LoanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            book = Book.objects.get(pk=serializer.validated_data["book_id"])
        except Book.DoesNotExist:
            return Response(
                {"status": "error", "message": "Libro no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        service = LoanService()
        try:
            loan = service.borrow_book(
                user=request.user,
                book=book,
                notes=serializer.validated_data.get("notes", ""),
            )
        except (BookNotAvailableError, LoanLimitExceededError,
                UserHasOverdueLoanError) as e:
            return Response(
                {"status": "error", "code": e.code, "message": e.message},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        out_serializer = LoanSerializer(loan, context={"request": request})
        return Response(
            {"status": "success", "message": "Préstamo creado exitosamente.", "data": out_serializer.data},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(summary="Devolver libro")
    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        loan = self.get_object()
        self.check_object_permissions(request, loan)

        service = LoanService()
        try:
            loan = service.return_book(loan)
        except LoanAlreadyReturnedError as e:
            return Response(
                {"status": "error", "code": e.code, "message": e.message},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        out = LoanSerializer(loan, context={"request": request})
        return Response(
            {"status": "success", "message": "Libro devuelto correctamente.", "data": out.data}
        )

    @extend_schema(summary="Renovar préstamo")
    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        loan = self.get_object()
        self.check_object_permissions(request, loan)

        service = LoanService()
        try:
            loan = service.renew_loan(loan)
        except (RenewalLimitExceededError, LoanAlreadyReturnedError) as e:
            return Response(
                {"status": "error", "code": e.code, "message": e.message},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        out = LoanSerializer(loan, context={"request": request})
        return Response(
            {"status": "success", "message": "Préstamo renovado exitosamente.", "data": out.data}
        )

    @extend_schema(summary="Préstamos vencidos (solo bibliotecarios)")
    @action(detail=False, methods=["get"], permission_classes=[IsLibrarian])
    def overdue(self, request):
        loans = LoanRepository.get_all_overdue()
        page = self.paginate_queryset(loans)
        if page is not None:
            serializer = LoanSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = LoanSerializer(loans, many=True, context={"request": request})
        return Response({"status": "success", "results": serializer.data})

    @extend_schema(summary="Historial de préstamos del usuario actual")
    @action(detail=False, methods=["get"])
    def history(self, request):
        loans = LoanRepository.get_all_by_user(request.user)
        page = self.paginate_queryset(loans)
        if page is not None:
            serializer = LoanSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = LoanSerializer(loans, many=True, context={"request": request})
        return Response({"status": "success", "results": serializer.data})
