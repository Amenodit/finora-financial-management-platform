from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class FinancialProfile(BaseModel):
    """
    A user's financial "workspace" — Personal, Family, Business, Travel, etc.
    Each profile has independent income/expense/savings data. A profile may
    optionally belong to a Family (see apps.families) for shared access.
    """

    PROFILE_TYPE_PERSONAL = "personal"
    PROFILE_TYPE_FAMILY = "family"
    PROFILE_TYPE_BUSINESS = "business"
    PROFILE_TYPE_CUSTOM = "custom"

    PROFILE_TYPE_CHOICES = [
        (PROFILE_TYPE_PERSONAL, "Personal"),
        (PROFILE_TYPE_FAMILY, "Family"),
        (PROFILE_TYPE_BUSINESS, "Business"),
        (PROFILE_TYPE_CUSTOM, "Custom"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="financial_profiles"
    )
    family = models.ForeignKey(
        "families.Family",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profiles",
    )
    name = models.CharField(max_length=100)
    profile_type = models.CharField(max_length=20, choices=PROFILE_TYPE_CHOICES, default=PROFILE_TYPE_PERSONAL)
    currency = models.CharField(max_length=3, default="INR")
    icon = models.CharField(max_length=32, blank=True, default="wallet")
    color = models.CharField(max_length=7, blank=True, default="#4F46E5")
    is_default = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_profile_name_per_owner",
            )
        ]
        indexes = [models.Index(fields=["owner", "profile_type"])]
        ordering = ["-is_default", "name"]

    def __str__(self):
        return f"{self.name} ({self.owner.email})"
