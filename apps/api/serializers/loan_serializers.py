"""Serializers for loans."""
from rest_framework import serializers
from apps.loans.models import Loan
from .book_serializers import BookListSerializer


class LoanSerializer(serializers.ModelSerializer):
    """Full loan serializer with nested book info."""
    book = BookListSerializer(read_only=True)
    book_id = serializers.UUIDField(write_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    calculated_fine = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Loan
        fields = [
            "id", "user_email", "user_name",
            "book", "book_id",
            "loan_date", "due_date", "return_date",
            "status", "status_display",
            "fine_amount", "fine_paid", "calculated_fine",
            "renewal_count", "notes",
            "is_overdue", "days_overdue", "days_remaining",
            "created_at",
        ]
        read_only_fields = [
            "id", "loan_date", "due_date", "return_date", "status",
            "fine_amount", "renewal_count", "created_at",
        ]


class LoanCreateSerializer(serializers.Serializer):
    """Serializer for creating a new loan."""
    book_id = serializers.UUIDField()
    notes = serializers.CharField(max_length=500, required=False, default="")


class LoanReturnSerializer(serializers.Serializer):
    """Empty serializer for return action."""
    pass


class LoanRenewSerializer(serializers.Serializer):
    """Empty serializer for renewal action."""
    pass
