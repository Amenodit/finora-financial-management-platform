from rest_framework import serializers

from apps.profiles.models import FinancialProfile


class FinancialProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialProfile
        fields = [
            "public_id", "name", "profile_type", "currency", "icon", "color",
            "is_default", "family", "created_at",
        ]
        read_only_fields = ["public_id", "created_at"]
