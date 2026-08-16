"""
All transaction mutations and financial arithmetic live here — never in
views, serializers, or JavaScript. This is the one place the formulas in
spec §71 are implemented, so dashboard, reports, and the API all agree.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import Sum

from apps.audit import services as audit
from apps.audit.models import AuditLog
from apps.transactions.models import Transaction


class DuplicateTransactionError(Exception):
    def __init__(self, existing_transaction):
        self.existing_transaction = existing_transaction
        super().__init__("Possible duplicate transaction detected.")


class StaleTransactionError(Exception):
    """Raised on optimistic-concurrency conflict: someone else edited this record first."""


@db_transaction.atomic
def create_transaction(*, profile, account, transaction_type, amount, transaction_date,
                        created_by, category=None, allow_duplicate=False, request=None, **extra):
    if amount is None or Decimal(amount) <= 0:
        raise ValidationError("Amount must be greater than zero.")

    candidate = Transaction(
        profile=profile,
        account=account,
        category=category,
        transaction_type=transaction_type,
        amount=amount,
        transaction_date=transaction_date,
        created_by=created_by,
        **extra,
    )
    signature = candidate.compute_duplicate_signature()

    if not allow_duplicate:
        existing = Transaction.objects.filter(profile=profile, duplicate_signature=signature).first()
        if existing:
            raise DuplicateTransactionError(existing)

    candidate.save()
    audit.record(created_by, AuditLog.ACTION_CREATE, candidate, request=request)
    return candidate


@db_transaction.atomic
def update_transaction(*, txn, expected_version, actor, request=None, **fields):
    """Optimistic concurrency: caller must pass the version they last read."""
    locked = Transaction.objects.select_for_update().get(pk=txn.pk)
    if locked.version != expected_version:
        raise StaleTransactionError(
            "This transaction was modified by someone else. Reload and try again."
        )

    for field, value in fields.items():
        setattr(locked, field, value)
    locked.version += 1
    locked.save()
    audit.record(actor, AuditLog.ACTION_UPDATE, locked, metadata={"fields": list(fields)}, request=request)
    return locked


def delete_transaction(*, txn, actor, request=None):
    txn.delete()  # soft delete
    audit.record(actor, AuditLog.ACTION_DELETE, txn, request=request)


# --- Financial calculation rules (spec §71) — the single source of truth ---

def total_income(profile, start_date=None, end_date=None, account=None):
    return _sum_by_type(profile, Transaction.TYPE_CREDIT, start_date, end_date, account)


def total_expenses(profile, start_date=None, end_date=None, account=None):
    return _sum_by_type(profile, Transaction.TYPE_DEBIT, start_date, end_date, account)


def savings(profile, start_date=None, end_date=None, account=None):
    return total_income(profile, start_date, end_date, account) - total_expenses(
        profile, start_date, end_date, account
    )


def savings_rate(profile, start_date=None, end_date=None, account=None):
    income = total_income(profile, start_date, end_date, account)
    if income == 0:
        return Decimal("0.00")
    return (savings(profile, start_date, end_date, account) / income * 100).quantize(Decimal("0.01"))


def category_spending(profile, start_date=None, end_date=None):
    qs = _scoped_queryset(profile, Transaction.TYPE_DEBIT, start_date, end_date)
    return (
        qs.values("category__id", "category__name", "category__color")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )


def _sum_by_type(profile, txn_type, start_date, end_date, account):
    qs = _scoped_queryset(profile, txn_type, start_date, end_date, account)
    return qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")


def _scoped_queryset(profile, txn_type, start_date, end_date, account=None):
    qs = Transaction.objects.filter(profile=profile, transaction_type=txn_type)
    if start_date:
        qs = qs.filter(transaction_date__gte=start_date)
    if end_date:
        qs = qs.filter(transaction_date__lte=end_date)
    if account:
        qs = qs.filter(account=account)
    return qs
