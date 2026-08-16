from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.transactions.api.serializers import DuplicateWarningSerializer, TransactionSerializer
from apps.transactions.models import Transaction
from apps.transactions.services import transaction_service


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Transaction lists must never be loaded unpaginated (spec §60) —
    pagination is applied globally via DEFAULT_PAGINATION_CLASS.
    """

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    filterset_fields = ["profile__public_id", "account__public_id", "category__public_id", "transaction_type"]
    search_fields = ["description", "merchant", "reference_number"]
    ordering_fields = ["transaction_date", "amount", "created_at"]

    def get_queryset(self):
        qs = Transaction.objects.filter(profile__owner=self.request.user)
        start = self.request.query_params.get("start_date")
        end = self.request.query_params.get("end_date")
        if start:
            qs = qs.filter(transaction_date__gte=start)
        if end:
            qs = qs.filter(transaction_date__lte=end)
        search = self.request.query_params.get("search")
        if search:
            from django.db.models import Q

            qs = qs.filter(
                Q(description__icontains=search) | Q(merchant__icontains=search) | Q(reference_number__icontains=search)
            )
        return qs.select_related("profile", "account", "category")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        allow_duplicate = str(request.data.get("allow_duplicate", "")).lower() in ("1", "true", "yes")

        try:
            txn = transaction_service.create_transaction(
                created_by=request.user,
                allow_duplicate=allow_duplicate,
                request=request,
                **serializer.validated_data,
            )
        except transaction_service.DuplicateTransactionError as exc:
            payload = DuplicateWarningSerializer(
                {
                    "detail": "Possible duplicate detected.",
                    "existing_transaction": exc.existing_transaction,
                },
                context=self.get_serializer_context(),
            ).data
            return Response(payload, status=status.HTTP_409_CONFLICT)
        except DjangoValidationError as exc:
            raise ValidationError({"amount": exc.messages})

        return Response(self.get_serializer(txn).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        expected_version = request.data.get("version", instance.version)
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)

        try:
            txn = transaction_service.update_transaction(
                txn=instance,
                expected_version=int(expected_version),
                actor=request.user,
                request=request,
                **{k: v for k, v in serializer.validated_data.items()},
            )
        except transaction_service.StaleTransactionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(self.get_serializer(txn).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        transaction_service.delete_transaction(txn=instance, actor=request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Quick totals for the currently filtered queryset's profile/date range — used by dashboard widgets."""
        profile_id = request.query_params.get("profile")
        if not profile_id:
            raise ValidationError({"profile": "Required query param."})

        from apps.profiles.models import FinancialProfile

        profile = FinancialProfile.objects.filter(owner=request.user, public_id=profile_id).first()
        if not profile:
            raise ValidationError({"profile": "Not found."})

        start = request.query_params.get("start_date")
        end = request.query_params.get("end_date")

        income = transaction_service.total_income(profile, start, end)
        expenses = transaction_service.total_expenses(profile, start, end)
        return Response(
            {
                "income": income,
                "expenses": expenses,
                "savings": income - expenses,
                "savings_rate": transaction_service.savings_rate(profile, start, end),
                "category_spending": list(transaction_service.category_spending(profile, start, end)),
            }
        )
