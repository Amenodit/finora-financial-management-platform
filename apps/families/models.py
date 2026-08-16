from django.conf import settings
from django.db import models

from apps.common.models import BaseModel, TimeStampedModel, UUIDPublicIDModel


class Family(BaseModel):
    """A household/family group. Owner is set at creation; ownership can be transferred."""

    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_families"
    )

    def __str__(self):
        return self.name


class FamilyMembership(BaseModel):
    """
    Role-based membership. Permissions are derived from `role` and enforced
    server-side (see apps.common.permissions) — never trust the frontend to
    hide an action instead of the API rejecting it.
    """

    ROLE_OWNER = "owner"
    ROLE_ADMIN = "administrator"
    ROLE_MEMBER = "member"
    ROLE_VIEWER = "viewer"

    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_ADMIN, "Administrator"),
        (ROLE_MEMBER, "Member"),
        (ROLE_VIEWER, "Viewer"),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="family_memberships"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    # If False, this member's personal transactions in the family profile are
    # private and not visible to other family members (see spec §65).
    share_transactions_with_family = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["family", "user"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_membership",
            )
        ]

    def __str__(self):
        return f"{self.user.email} in {self.family.name} ({self.role})"


class FamilyInvitation(UUIDPublicIDModel, TimeStampedModel):
    """
    Email-based invitation, accepted via a signed token link. Kept separate
    from FamilyMembership since an invitation may never be accepted/may expire.
    """

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_DECLINED = "declined"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_DECLINED, "Declined"),
        (STATUS_EXPIRED, "Expired"),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="invitations")
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_invitations"
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=FamilyMembership.ROLE_CHOICES, default=FamilyMembership.ROLE_MEMBER)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["email", "status"])]
