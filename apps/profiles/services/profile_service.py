from django.core.exceptions import ValidationError

from apps.audit import services as audit
from apps.audit.models import AuditLog
from apps.profiles.models import FinancialProfile


def create_default_profile(user):
    return FinancialProfile.objects.create(
        owner=user,
        name="Personal",
        profile_type=FinancialProfile.PROFILE_TYPE_PERSONAL,
        currency=user.preferred_currency or "INR",
        is_default=True,
    )


def create_profile(*, owner, name, profile_type, currency=None, request=None, **extra):
    if FinancialProfile.objects.filter(owner=owner, name=name).exists():
        raise ValidationError("A profile with this name already exists.")

    profile = FinancialProfile.objects.create(
        owner=owner,
        name=name,
        profile_type=profile_type,
        currency=currency or owner.preferred_currency or "INR",
        **extra,
    )
    audit.record(owner, AuditLog.ACTION_CREATE, profile, request=request)
    return profile


def delete_profile(*, profile, actor, request=None):
    """Soft-delete only — never hard-delete a profile that may have financial history."""
    profile.delete()
    audit.record(actor, AuditLog.ACTION_DELETE, profile, request=request)
