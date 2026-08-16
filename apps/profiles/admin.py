from django.contrib import admin

from apps.profiles.models import FinancialProfile


@admin.register(FinancialProfile)
class FinancialProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "profile_type", "currency", "family", "is_default", "created_at"]
    list_filter = ["profile_type", "currency"]
    search_fields = ["name", "owner__email"]
    autocomplete_fields = ["owner", "family"]
