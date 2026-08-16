from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.profiles.api.serializers import FinancialProfileSerializer
from apps.profiles.models import FinancialProfile
from apps.profiles.services import profile_service


class FinancialProfileViewSet(viewsets.ModelViewSet):
    """
    A user only ever sees their own profiles here. Family-shared profiles are
    still owned by one user; other members reach them through the family
    endpoints, which apply role-based checks explicitly.
    """

    serializer_class = FinancialProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"

    def get_queryset(self):
        return FinancialProfile.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        try:
            profile = profile_service.create_profile(
                owner=self.request.user, request=self.request, **serializer.validated_data
            )
        except DjangoValidationError as exc:
            raise ValidationError({"name": exc.messages})
        serializer.instance = profile

    def perform_destroy(self, instance):
        profile_service.delete_profile(profile=instance, actor=self.request.user, request=self.request)
