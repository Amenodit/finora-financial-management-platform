from django.contrib import admin

from apps.audit.models import AuditLog, RequestLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor", "action", "target_model", "target_id", "ip_address"]
    list_filter = ["action", "target_model"]
    search_fields = ["target_id", "actor__email"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # audit logs are append-only


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "user", "method", "path", "status_code", "duration_ms"]
    list_filter = ["method", "status_code"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
