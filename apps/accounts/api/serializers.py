from rest_framework import serializers

from apps.accounts.models import Account
from apps.profiles.models import FinancialProfile


class AccountSerializer(serializers.ModelSerializer):
    profile = serializers.SlugRelatedField(slug_field="public_id", queryset=FinancialProfile.objects.all())

    class Meta:
        model = Account
        fields = [
            "public_id", "profile", "name", "account_type", "institution",
            "last_four_digits", "currency", "opening_balance", "current_balance",
            "status", "color", "icon", "created_at",
        ]
        read_only_fields = ["public_id", "current_balance", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None:
            self.fields["profile"].queryset = FinancialProfile.objects.filter(owner=request.user)

    def create(self, validated_data):
        # On creation, current_balance starts equal to opening_balance.
        validated_data["current_balance"] = validated_data.get("opening_balance", 0)
        return super().create(validated_data)
