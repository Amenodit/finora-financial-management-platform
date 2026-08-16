from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "is_staff", "mfa_enabled", "is_active", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["public_id", "last_login", "date_joined", "failed_login_attempts", "locked_until"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number", "date_of_birth", "profile_image")}),
        ("Preferences", {"fields": ("preferred_currency", "country", "timezone")}),
        ("Security", {"fields": ("mfa_enabled", "failed_login_attempts", "locked_until", "last_login_ip")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
