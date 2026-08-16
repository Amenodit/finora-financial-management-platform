import pytest

from apps.categories.models import Category, CategoryRule

pytestmark = pytest.mark.django_db


def test_default_categories_seeded():
    assert Category.objects.filter(is_system_default=True, kind="expense").count() >= 15
    assert Category.objects.filter(is_system_default=True, kind="income").count() >= 5


def test_default_categorization_rules_seeded():
    assert CategoryRule.objects.filter(keyword="SWIGGY").exists()
    rule = CategoryRule.objects.get(keyword="SWIGGY")
    assert rule.category.name == "Food"
