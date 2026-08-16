import pytest
from django.db import connection

from apps.accounts.models import Account
from apps.profiles.models import FinancialProfile
from apps.users.services import auth_service

pytestmark = pytest.mark.django_db


def test_last_four_digits_encrypted_at_rest():
    user = auth_service.register_user(email="enc_test@example.com", password="CorrectHorse99!")
    profile = FinancialProfile.objects.filter(owner=user).first()
    account = Account.objects.create(
        profile=profile, name="Encrypted Test", account_type=Account.TYPE_BANK_SAVINGS,
        last_four_digits="9876",
    )

    # Raw DB value must not equal the plaintext.
    with connection.cursor() as cursor:
        cursor.execute("SELECT last_four_digits FROM accounts_account WHERE id = %s", [account.id])
        raw_value = cursor.fetchone()[0]
    assert raw_value != "9876"
    assert "9876" not in raw_value

    # ORM access must transparently decrypt.
    account.refresh_from_db()
    assert account.last_four_digits == "9876"


def test_phone_number_encrypted_at_rest():
    user = auth_service.register_user(
        email="enc_phone@example.com", password="CorrectHorse99!", phone_number="+919876543210"
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT phone_number FROM users_user WHERE id = %s", [user.id])
        raw_value = cursor.fetchone()[0]
    assert "9876543210" not in raw_value

    user.refresh_from_db()
    assert user.phone_number == "+919876543210"
