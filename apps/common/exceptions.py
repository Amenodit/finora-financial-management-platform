import logging

from rest_framework.views import exception_handler

logger = logging.getLogger("apps")


def api_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler so every API error response has a
    consistent shape: {"error": {"code": ..., "message": ..., "details": ...}}
    and unhandled exceptions never leak internal tracebacks to the client.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "error": {
                "code": response.status_code,
                "message": _extract_message(response.data),
                "details": response.data,
            }
        }
        response.data = error_payload
        return response

    # Unhandled exception: log full detail server-side, return a generic message.
    logger.exception("Unhandled exception in API view", extra={"context": str(context.get("view"))})
    return None


def _extract_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        return "Request could not be processed."
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)
