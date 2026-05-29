"""Admin configuration for notifications app."""
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user_email", "type", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("title", "user__email", "message")
    readonly_fields = ("created_at",)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Usuario"
