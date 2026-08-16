import hashlib
import re
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.accounts.models import Account
from apps.categories.models import Category
from apps.common.models import BaseModel
from apps.profiles.models import FinancialProfile


class Transaction(BaseModel):
    """
    The core financial record. Amount is always stored positive; direction is
    carried by `transaction_type` (spec §70) rather than sign, so summation
    logic can't silently go wrong from a stray negative number.

    All monetary values use Decimal — never float — end to end.
    """

    TYPE_CREDIT = "credit"
    TYPE_DEBIT = "debit"

    TYPE_CHOICES = [
        (TYPE_CREDIT, "Credit (Income)"),
        (TYPE_DEBIT, "Debit (Expense)"),
    ]

    SOURCE_MANUAL = "manual"
    SOURCE_IMPORT = "import"
    SOURCE_RECURRING = "recurring"

    SOURCE_CHOICES = [
        (SOURCE_MANUAL, "Manual Entry"),
        (SOURCE_IMPORT, "Bank Statement Import"),
        (SOURCE_RECURRING, "Recurring Transaction"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("upi", "UPI"),
        ("debit_card", "Debit Card"),
        ("credit_card", "Credit Card"),
        ("netbanking", "Net Banking"),
        ("cheque", "Cheque"),
        ("auto_debit", "Auto Debit"),
        ("other", "Other"),
    ]

    profile = models.ForeignKey(FinancialProfile, on_delete=models.CASCADE, related_name="transactions")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="transactions"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_transactions"
    )

    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=3, default="INR")

    transaction_date = models.DateField(db_index=True)
    value_date = models.DateField(null=True, blank=True)

    description = models.CharField(max_length=500, blank=True, default="")
    merchant = models.CharField(max_length=200, blank=True, default="", db_index=True)
    subcategory = models.CharField(max_length=100, blank=True, default="")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, default="")
    reference_number = models.CharField(max_length=100, blank=True, default="", db_index=True)
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, default="")

    balance_after = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    import_batch_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Family visibility (spec §65): a member can mark their own transaction
    # private even within a shared family profile.
    is_private = models.BooleanField(default=False)

    # Duplicate-detection signature (spec §21): profile+account+date+amount+
    # type+reference+normalized description, hashed for a fast indexed lookup.
    duplicate_signature = models.CharField(max_length=64, db_index=True, editable=False)

    # Optimistic concurrency: two family members editing the same transaction
    # at once shouldn't silently overwrite one another (spec gap noted for family editing).
    version = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["profile", "transaction_date"]),
            models.Index(fields=["profile", "transaction_type", "transaction_date"]),
            models.Index(fields=["account", "transaction_date"]),
            models.Index(fields=["category"]),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name="transaction_amount_positive"),
        ]
        ordering = ["-transaction_date", "-created_at"]

    def __str__(self):
        return f"{self.transaction_type} {self.amount} {self.currency} on {self.transaction_date}"

    def compute_duplicate_signature(self):
        normalized_description = re.sub(r"\s+", " ", (self.description or "").strip().lower())
        raw = "|".join(
            [
                str(self.profile_id),
                str(self.account_id),
                str(self.transaction_date),
                str(self.amount),
                self.transaction_type,
                self.reference_number or "",
                normalized_description,
            ]
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def save(self, *args, **kwargs):
        self.duplicate_signature = self.compute_duplicate_signature()
        super().save(*args, **kwargs)
