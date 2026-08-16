from apps.audit.models import AuditLog


def record(actor, action, target, metadata=None, request=None):
    """
    Central entry point for writing audit trail entries. Service classes
    call this after a successful mutation — never the view layer directly —
    so audit coverage doesn't depend on remembering to add it per-endpoint.
    """
    ip_address = None
    user_agent = ""
    if request is not None:
        ip_address = _client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:300]

    AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        target_model=target.__class__.__name__,
        target_id=str(getattr(target, "public_id", getattr(target, "pk", target))),
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata or {},
    )


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
