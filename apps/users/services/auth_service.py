"""
Authentication business logic, kept out of views/serializers so it can be
reused by both the API and any future Django-template login form, and so it
has one place to unit test lockout/MFA behaviour.
"""
import pyotp
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.audit import services as audit
from apps.audit.models import AuditLog
from apps.profiles.services.profile_service import create_default_profile

User = get_user_model()

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class AuthenticationError(Exception):
    pass


class AccountLockedError(AuthenticationError):
    pass


class MFARequiredError(AuthenticationError):
    """Raised when password is correct but a TOTP code is still needed."""


def register_user(*, email, password, first_name="", last_name="", **extra_fields):
    email = email.strip().lower()
    if User.objects.filter(email=email).exists():
        raise ValidationError("An account with this email already exists.")

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        **extra_fields,
    )
    # Every user gets a default "Personal" financial profile on signup —
    # matches the expected workflow in the spec (register -> create profile).
    create_default_profile(user)
    audit.record(user, AuditLog.ACTION_CREATE, user, metadata={"event": "user_registered"})
    return user


def authenticate_credentials(*, email, password, mfa_code=None, request=None):
    email = (email or "").strip().lower()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Deliberately identical error/timing profile to "wrong password" —
        # don't leak whether an email is registered.
        raise AuthenticationError("Invalid email or password.")

    if user.is_locked:
        audit.record(user, AuditLog.ACTION_LOGIN_FAILED, user, metadata={"reason": "locked"}, request=request)
        raise AccountLockedError(
            f"Account temporarily locked due to repeated failed attempts. Try again after {LOCKOUT_MINUTES} minutes."
        )

    if not check_password(password, user.password):
        _register_failed_attempt(user)
        audit.record(user, AuditLog.ACTION_LOGIN_FAILED, user, metadata={"reason": "bad_password"}, request=request)
        raise AuthenticationError("Invalid email or password.")

    if user.mfa_enabled:
        if not mfa_code:
            raise MFARequiredError("MFA code required.")
        if not verify_totp(user, mfa_code):
            _register_failed_attempt(user)
            audit.record(user, AuditLog.ACTION_LOGIN_FAILED, user, metadata={"reason": "bad_mfa"}, request=request)
            raise AuthenticationError("Invalid MFA code.")

    # Success — reset lockout counters.
    user.failed_login_attempts = 0
    user.locked_until = None
    if request is not None:
        user.last_login_ip = _client_ip(request)
    user.save(update_fields=["failed_login_attempts", "locked_until", "last_login_ip"])
    audit.record(user, AuditLog.ACTION_LOGIN, user, request=request)
    return user


def _register_failed_attempt(user):
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = timezone.now() + timezone.timedelta(minutes=LOCKOUT_MINUTES)
    user.save(update_fields=["failed_login_attempts", "locked_until"])


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# --- MFA (TOTP) ---

def start_mfa_enrollment(user):
    """Generates a new TOTP secret (not yet activated until confirmed)."""
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    user.mfa_enabled = False
    user.save(update_fields=["mfa_secret", "mfa_enabled"])
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Finora")
    return secret, uri


def confirm_mfa_enrollment(user, code):
    if not user.mfa_secret or not verify_totp(user, code):
        raise ValidationError("Invalid verification code.")
    user.mfa_enabled = True
    codes = [pyotp.random_base32()[:10] for _ in range(8)]
    user.mfa_backup_codes = [make_password(c) for c in codes]
    user.save(update_fields=["mfa_enabled", "mfa_backup_codes"])
    return codes  # shown once, raw, to the user — never stored raw


def verify_totp(user, code):
    if not user.mfa_secret:
        return False
    totp = pyotp.totp.TOTP(user.mfa_secret)
    return totp.verify(code, valid_window=1)


def disable_mfa(user):
    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_backup_codes = []
    user.save(update_fields=["mfa_enabled", "mfa_secret", "mfa_backup_codes"])
