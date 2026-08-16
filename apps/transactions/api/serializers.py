from rest_framework import serializers

from apps.accounts.models import Account
from apps.categories.models import Category
from apps.profiles.models import FinancialProfile
from apps.transactions.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    profile = serializers.SlugRelatedField(slug_field="public_id", queryset=FinancialProfile.objects.all())
    account = serializers.SlugRelatedField(slug_field="public_id", queryset=Account.objects.all())
    category = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Category.objects.all(), required=False, allow_null=True
    )
    version = serializers.IntegerField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "public_id", "profile", "account", "category", "transaction_type", "amount",
            "currency", "transaction_date", "value_date", "description", "merchant",
            "subcategory", "payment_method", "reference_number", "tags", "notes",
            "source", "is_private", "version", "created_at",
        ]
        read_only_fields = ["public_id", "source", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None:
            self.fields["profile"].queryset = FinancialProfile.objects.filter(owner=request.user)
            self.fields["account"].queryset = Account.objects.filter(profile__owner=request.user)


class DuplicateWarningSerializer(serializers.Serializer):
    detail = serializers.CharField()
    existing_transaction = TransactionSerializer()
