"""
Account creation/mutation logic, kept out of views so the web UI and the API
serializer's create() path can eventually share it without duplication.
"""
from apps.accounts.models import Account
from apps.audit import services as audit
from apps.audit.models import AuditLog


def create_account(*, profile, name, account_type, institution="", currency=None,
                    opening_balance=0, last_four_digits=None, actor=None, request=None):
    account = Account.objects.create(
        profile=profile,
        name=name,
        account_type=account_type,
        institution=institution,
        currency=currency or profile.currency,
        opening_balance=opening_balance,
        current_balance=opening_balance,  # balance starts equal to opening balance
        last_four_digits=last_four_digits,
    )
    if actor is not None:
        audit.record(actor, AuditLog.ACTION_CREATE, account, request=request)
    return account


def close_account(*, account, actor, request=None):
    account.status = Account.STATUS_CLOSED
    account.save(update_fields=["status"])
    audit.record(actor, AuditLog.ACTION_UPDATE, account, metadata={"event": "closed"}, request=request)
