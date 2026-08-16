import logging
import time

from apps.audit.models import RequestLog

security_logger = logging.getLogger("security")


class RequestAuditMiddleware:
    """
    Logs every request's timing/status for the API surface, and flags
    authentication failures to the security logger so brute-force patterns
    are visible without needing an external SIEM from day one.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        if request.path.startswith("/api/"):
            try:
                RequestLog.objects.create(
                    user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
                    method=request.method,
                    path=request.path[:500],
                    status_code=response.status_code,
                    ip_address=self._client_ip(request),
                    duration_ms=duration_ms,
                )
            except Exception:
                # Never let audit logging break the response.
                security_logger.exception("Failed to write RequestLog")

            if response.status_code in (401, 403):
                security_logger.warning(
                    "Auth failure: %s %s from %s (status %s)",
                    request.method,
                    request.path,
                    self._client_ip(request),
                    response.status_code,
                )

        return response

    @staticmethod
    def _client_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
