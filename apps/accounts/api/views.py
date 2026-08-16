from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.api.serializers import AccountSerializer
from apps.accounts.models import Account


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    filterset_fields = ["account_type", "status", "profile__public_id"]

    def get_queryset(self):
        return Account.objects.filter(profile__owner=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
