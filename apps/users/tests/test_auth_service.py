import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.users.services import auth_service

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_register_user_creates_default_profile():
    user = auth_service.register_user(email="Alice@Example.com", password="CorrectHorse99!")
    assert user.email == "alice@example.com"  # normalized to lowercase
    assert user.financial_profiles.count() == 1
    assert user.financial_profiles.first().is_default is True


def test_register_duplicate_email_rejected():
    auth_service.register_user(email="bob@example.com", password="CorrectHorse99!")
    with pytest.raises(ValidationError):
        auth_service.register_user(email="bob@example.com", password="AnotherPass99!")


def test_authenticate_wrong_password_increments_failed_attempts():
    auth_service.register_user(email="carol@example.com", password="CorrectHorse99!")
    for _ in range(3):
        with pytest.raises(auth_service.AuthenticationError):
            auth_service.authenticate_credentials(email="carol@example.com", password="wrong")
    user = User.objects.get(email="carol@example.com")
    assert user.failed_login_attempts == 3


def test_account_locks_after_max_failed_attempts():
    auth_service.register_user(email="dave@example.com", password="CorrectHorse99!")
    for _ in range(auth_service.MAX_FAILED_ATTEMPTS):
        try:
            auth_service.authenticate_credentials(email="dave@example.com", password="wrong")
        except auth_service.AuthenticationError:
            pass

    user = User.objects.get(email="dave@example.com")
    assert user.is_locked

    with pytest.raises(auth_service.AccountLockedError):
        auth_service.authenticate_credentials(email="dave@example.com", password="CorrectHorse99!")


def test_successful_login_resets_failed_attempts():
    auth_service.register_user(email="erin@example.com", password="CorrectHorse99!")
    try:
        auth_service.authenticate_credentials(email="erin@example.com", password="wrong")
    except auth_service.AuthenticationError:
        pass

    user = auth_service.authenticate_credentials(email="erin@example.com", password="CorrectHorse99!")
    assert user.failed_login_attempts == 0


def test_mfa_enrollment_and_login_flow():
    import pyotp

    user = auth_service.register_user(email="frank@example.com", password="CorrectHorse99!")
    secret, uri = auth_service.start_mfa_enrollment(user)
    assert user.mfa_enabled is False  # not active until confirmed

    code = pyotp.TOTP(secret).now()
    backup_codes = auth_service.confirm_mfa_enrollment(user, code)
    assert len(backup_codes) == 8
    user.refresh_from_db()
    assert user.mfa_enabled is True

    # Login without MFA code should now require it.
    with pytest.raises(auth_service.MFARequiredError):
        auth_service.authenticate_credentials(email="frank@example.com", password="CorrectHorse99!")

    # Login with a valid TOTP code succeeds.
    valid_code = pyotp.TOTP(user.mfa_secret).now()
    logged_in = auth_service.authenticate_credentials(
        email="frank@example.com", password="CorrectHorse99!", mfa_code=valid_code
    )
    assert logged_in.email == "frank@example.com"
