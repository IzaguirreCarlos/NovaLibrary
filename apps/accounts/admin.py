"""Admin configuration for accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email", "full_name", "role_badge", "membership_number",
        "is_active", "date_joined"
    )
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name", "membership_number")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "membership_number", "membership_date")

    fieldsets = (
        ("Credenciales", {"fields": ("email", "username", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "avatar", "phone", "bio")}),
        ("Membresía", {"fields": ("role", "membership_number", "membership_date")}),
        ("Preferencias", {"fields": ("dark_mode", "email_notifications")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Actividad", {"fields": ("date_joined", "last_login"), "classes": ("collapse",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "first_name", "last_name", "role", "password1", "password2"),
        }),
    )

    def role_badge(self, obj):
        colors = {"admin": "#ef4444", "librarian": "#3b82f6", "member": "#10b981"}
        color = colors.get(obj.role, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:12px;font-size:11px">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = "Rol"
