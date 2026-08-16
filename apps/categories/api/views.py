from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.categories.api.serializers import CategorySerializer
from apps.categories.models import Category


class CategoryViewSet(viewsets.ModelViewSet):
    """Returns system-default categories plus the current user's own custom ones."""

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    filterset_fields = ["kind"]

    def get_queryset(self):
        return Category.objects.filter(Q(owner=self.request.user) | Q(owner__isnull=True))

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, is_system_default=False)

    def perform_update(self, serializer):
        if serializer.instance.owner_id is None:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("System default categories cannot be modified.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner_id is None:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("System default categories cannot be deleted.")
        instance.delete()
