from rest_framework import serializers

from apps.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["public_id", "name", "kind", "parent", "icon", "color", "is_system_default"]
        read_only_fields = ["public_id", "is_system_default"]
