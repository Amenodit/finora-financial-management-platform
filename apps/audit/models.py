from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class AuditLog(TimeStampedModel):
    """
    Append-only record of who did what to which financial object. Written by
    the service layer (not views directly) so every mutation path is covered
    consistently. This table is never soft-deleted or edited after creation.
    """

    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_RESTORE = "restore"
    ACTION_LOGIN = "login"
    ACTION_LOGIN_FAILED = "login_failed"
    ACTION_IMPORT = "import"
    ACTION_EXPORT = "export"

    ACTION_CHOICES = [
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_DELETE, "Delete"),
        (ACTION_RESTORE, "Restore"),
        (ACTION_LOGIN, "Login"),
        (ACTION_LOGIN_FAILED, "Login Failed"),
        (ACTION_IMPORT, "Import"),
        (ACTION_EXPORT, "Export"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    target_model = models.CharField(max_length=100, db_index=True)
    target_id = models.CharField(max_length=100, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target_model", "target_id"]),
            models.Index(fields=["actor", "action"]),
        ]

    def __str__(self):
        return f"{self.actor_id} {self.action} {self.target_model}:{self.target_id}"


class RequestLog(models.Model):
    """
    Lightweight record of API requests for security monitoring — separate
    from AuditLog, which is about domain-object mutations.
    """

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
