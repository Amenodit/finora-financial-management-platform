from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import Account
from apps.profiles.models import FinancialProfile
from apps.transactions.services import transaction_service
from apps.users.services import auth_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def profile_and_account():
    user = auth_service.register_user(email="txn_tester@example.com", password="CorrectHorse99!")
    profile = FinancialProfile.objects.filter(owner=user).first()
    account = Account.objects.create(
        profile=profile, name="Test Bank", account_type=Account.TYPE_BANK_SAVINGS,
        currency="INR", opening_balance=Decimal("1000.00"), current_balance=Decimal("1000.00"),
    )
    return user, profile, account


def test_create_transaction_success(profile_and_account):
    user, profile, account = profile_and_account
    txn = transaction_service.create_transaction(
        profile=profile, account=account, transaction_type="debit",
        amount=Decimal("100.00"), transaction_date="2026-08-01",
        created_by=user, description="Test purchase",
    )
    assert txn.amount == Decimal("100.00")
    assert txn.version == 0


def test_zero_amount_rejected(profile_and_account):
    user, profile, account = profile_and_account
    with pytest.raises(ValidationError):
        transaction_service.create_transaction(
            profile=profile, account=account, transaction_type="debit",
            amount=Decimal("0.00"), transaction_date="2026-08-01", created_by=user,
        )


def test_duplicate_transaction_detected(profile_and_account):
    user, profile, account = profile_and_account
    transaction_service.create_transaction(
        profile=profile, account=account, transaction_type="debit",
        amount=Decimal("250.00"), transaction_date="2026-08-05",
        created_by=user, description="Grocery run", reference_number="REF001",
    )
    with pytest.raises(transaction_service.DuplicateTransactionError) as exc_info:
        transaction_service.create_transaction(
            profile=profile, account=account, transaction_type="debit",
            amount=Decimal("250.00"), transaction_date="2026-08-05",
            created_by=user, description="Grocery run", reference_number="REF001",
        )
    assert exc_info.value.existing_transaction.description == "Grocery run"


def test_duplicate_can_be_forced_through(profile_and_account):
    user, profile, account = profile_and_account
    transaction_service.create_transaction(
        profile=profile, account=account, transaction_type="debit",
        amount=Decimal("250.00"), transaction_date="2026-08-05",
        created_by=user, description="Grocery run", reference_number="REF001",
    )
    txn2 = transaction_service.create_transaction(
        profile=profile, account=account, transaction_type="debit",
        amount=Decimal("250.00"), transaction_date="2026-08-05",
        created_by=user, description="Grocery run", reference_number="REF001",
        allow_duplicate=True,
    )
    assert txn2 is not None


def test_optimistic_concurrency_conflict(profile_and_account):
    user, profile, account = profile_and_account
    txn = transaction_service.create_transaction(
        profile=profile, account=account, transaction_type="debit",
        amount=Decimal("50.00"), transaction_date="2026-08-01", created_by=user,
    )
    # First update with correct version succeeds and bumps version to 1.
    updated = transaction_service.update_transaction(
        txn=txn, expected_version=0, actor=user, amount=Decimal("60.00")
    )
    assert updated.version == 1

    # A second update using the now-stale version=0 must fail.
    with pytest.raises(transaction_service.StaleTransactionError):
        transaction_service.update_transaction(
            txn=txn, expected_version=0, actor=user, amount=Decimal("70.00")
        )


def test_soft_delete_excludes_from_default_manager(profile_and_account):
    from apps.transactions.models import Transaction

    user, profile, account = profile_and_account
    txn = transaction_service.create_transaction(
        profile=profile, account=account, transaction_type="debit",
        amount=Decimal("30.00"), transaction_date="2026-08-01", created_by=user,
    )
    transaction_service.delete_transaction(txn=txn, actor=user)

    assert Transaction.objects.filter(pk=txn.pk).count() == 0  # default manager excludes it
    assert Transaction.all_objects.filter(pk=txn.pk).count() == 1  # still in DB, soft-deleted
    assert Transaction.all_objects.get(pk=txn.pk).is_deleted is True


def test_financial_calculations(profile_and_account):
    user, profile, account = profile_and_account
    transaction_service.create_transaction(
        profile=profile, account=account, transaction_type="credit",
        amount=Decimal("1000.00"), transaction_date="2026-08-01", created_by=user,
    )
    transaction_service.create_transaction(
        profile=profile, account=account, transaction_type="debit",
        amount=Decimal("300.00"), transaction_date="2026-08-02", created_by=user,
    )

    assert transaction_service.total_income(profile) == Decimal("1000.00")
    assert transaction_service.total_expenses(profile) == Decimal("300.00")
    assert transaction_service.savings(profile) == Decimal("700.00")
    assert transaction_service.savings_rate(profile) == Decimal("70.00")


def test_amount_check_constraint_at_db_level(profile_and_account):
    """Even bypassing the service layer, the DB itself refuses non-positive amounts."""
    from django.db import IntegrityError, transaction as db_txn

    from apps.transactions.models import Transaction

    user, profile, account = profile_and_account
    with pytest.raises(IntegrityError):
        with db_txn.atomic():
            Transaction.objects.create(
                profile=profile, account=account, transaction_type="debit",
                amount=Decimal("-5.00"), transaction_date="2026-08-01", created_by=user,
            )
