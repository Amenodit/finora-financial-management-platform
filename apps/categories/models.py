from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Category(BaseModel):
    """
    Expense/income categories. `owner` is null for system-provided default
    categories (seeded via migration) and set for user-created custom ones.
    """

    KIND_EXPENSE = "expense"
    KIND_INCOME = "income"

    KIND_CHOICES = [
        (KIND_EXPENSE, "Expense"),
        (KIND_INCOME, "Income"),
    ]

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="subcategories"
    )
    icon = models.CharField(max_length=32, blank=True, default="tag")
    color = models.CharField(max_length=7, blank=True, default="#6B7280")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="custom_categories",
        help_text="Null for system default categories, set for user-created ones.",
    )
    is_system_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "categories"
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name", "kind"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_category_name_per_owner",
            )
        ]
        ordering = ["kind", "name"]

    def __str__(self):
        return f"{self.name} ({self.kind})"


class CategoryRule(BaseModel):
    """
    Rule-based auto-categorization: if a transaction description matches
    `keyword` (case-insensitive substring), assign `category`. Kept as data
    rather than code so it's user-extensible without a deploy, and so the
    engine can later be swapped for an ML classifier without changing callers.
    """

    keyword = models.CharField(max_length=100, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="rules")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="category_rules",
        help_text="Null for system-wide default rules.",
    )
    priority = models.PositiveSmallIntegerField(default=100, help_text="Lower runs first.")

    class Meta:
        ordering = ["priority", "keyword"]

    def __str__(self):
        return f"'{self.keyword}' -> {self.category.name}"
