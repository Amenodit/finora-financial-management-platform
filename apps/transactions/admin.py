from django.contrib import admin

from apps.transactions.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_date", "profile", "account", "transaction_type",
        "amount", "currency", "category", "merchant", "source",
    ]
    list_filter = ["transaction_type", "source", "currency", "is_private"]
    search_fields = ["description", "merchant", "reference_number"]
    date_hierarchy = "transaction_date"
    readonly_fields = ["duplicate_signature", "version", "public_id"]
