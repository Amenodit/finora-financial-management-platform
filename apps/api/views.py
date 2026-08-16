from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Used by load balancers / uptime monitors. Checks DB connectivity so a
    "healthy" response actually means the app can serve real requests.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_ok = False

        status_code = 200 if db_ok else 503
        return Response({"status": "ok" if db_ok else "degraded", "database": db_ok}, status=status_code)
