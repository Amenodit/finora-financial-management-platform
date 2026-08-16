from django.contrib import admin

from apps.accounts.models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["name", "profile", "account_type", "institution", "currency", "current_balance", "status"]
    list_filter = ["account_type", "status", "currency"]
    search_fields = ["name", "institution"]
    # last_four_digits is encrypted — never exposed as a searchable/list field.
