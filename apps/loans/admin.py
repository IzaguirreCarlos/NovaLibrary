"""Admin configuration for loans app."""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "book_title", "user_email", "status_badge", "loan_date",
        "due_date", "days_info", "fine_amount"
    )
    list_filter = ("status", "loan_date", "due_date")
    search_fields = ("book__title", "user__email", "book__isbn")
    raw_id_fields = ("user", "book")
    readonly_fields = ("created_at", "updated_at", "calculated_fine", "days_overdue")
    date_hierarchy = "loan_date"

    fieldsets = (
        ("Datos del préstamo", {"fields": ("user", "book", "loan_date", "due_date", "return_date")}),
        ("Estado", {"fields": ("status", "renewal_count", "notes")}),
        ("Multas", {"fields": ("fine_amount", "fine_paid", "calculated_fine", "days_overdue")}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def book_title(self, obj):
        return obj.book.title[:40]
    book_title.short_description = "Libro"

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Usuario"

    def status_badge(self, obj):
        colors = {
            "borrowed": "#3b82f6",
            "returned": "#10b981",
            "overdue": "#ef4444",
            "cancelled": "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:12px;font-size:11px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Estado"

    def days_info(self, obj):
        if obj.status == "borrowed":
            if obj.is_overdue:
                return format_html('<span style="color:red">Vencido ({} días)</span>', obj.days_overdue)
            return f"{obj.days_remaining} días restantes"
        return "-"
    days_info.short_description = "Tiempo"
