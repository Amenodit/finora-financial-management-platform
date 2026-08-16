from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from apps.common.fields import EncryptedTextField
from apps.common.models import BaseModel
from apps.profiles.models import FinancialProfile


class Account(BaseModel):
    """
    A financial account (bank savings, credit card, cash, UPI, wallet, etc.)
    within a profile. We deliberately never store banking credentials — only
    the last 4 digits (encrypted) for the user's own reference.
    """

    TYPE_BANK_SAVINGS = "bank_savings"
    TYPE_BANK_CURRENT = "bank_current"
    TYPE_CREDIT_CARD = "credit_card"
    TYPE_CASH = "cash"
    TYPE_UPI = "upi"
    TYPE_WALLET = "wallet"
    TYPE_INVESTMENT = "investment"
    TYPE_LOAN = "loan"
    TYPE_OTHER = "other"

    TYPE_CHOICES = [
        (TYPE_BANK_SAVINGS, "Bank Savings"),
        (TYPE_BANK_CURRENT, "Bank Current"),
        (TYPE_CREDIT_CARD, "Credit Card"),
        (TYPE_CASH, "Cash"),
        (TYPE_UPI, "UPI"),
        (TYPE_WALLET, "Wallet"),
        (TYPE_INVESTMENT, "Investment Account"),
        (TYPE_LOAN, "Loan"),
        (TYPE_OTHER, "Other"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_CLOSED, "Closed"),
    ]

    profile = models.ForeignKey(FinancialProfile, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    institution = models.CharField(max_length=100, blank=True, default="")
    last_four_digits = EncryptedTextField(
        null=True,
        blank=True,
        validators=[RegexValidator(r"^\d{4}$", "Must be exactly 4 digits.")],
    )
    currency = models.CharField(max_length=3, default="INR")
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    color = models.CharField(max_length=7, blank=True, default="#0EA5E9")
    icon = models.CharField(max_length=32, blank=True, default="landmark")

    class Meta:
        indexes = [models.Index(fields=["profile", "status"])]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"
