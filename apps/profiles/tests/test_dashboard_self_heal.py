"""
Regression test for a real bug: a user created via `createsuperuser` (which
bypasses the registration flow and its automatic profile creation) hit a
dead-end "contact support" screen on first dashboard visit. The dashboard
should self-heal by creating a default profile instead.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.profiles.models import FinancialProfile

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_superuser_without_profile_gets_self_healed_on_dashboard_visit():
    user = User.objects.create_superuser(email="admin_only@example.com", password="AdminPass123!")
    assert user.financial_profiles.count() == 0

    client = Client()
    client.login(email="admin_only@example.com", password="AdminPass123!")

    response = client.get("/", follow=True)

    assert response.status_code == 200
    body = response.content.decode()
    assert "contact support" not in body.lower()
    assert FinancialProfile.objects.filter(owner=user).count() == 1


def test_dashboard_visit_is_idempotent_does_not_create_duplicate_profiles():
    user = User.objects.create_superuser(email="admin_only2@example.com", password="AdminPass123!")
    client = Client()
    client.login(email="admin_only2@example.com", password="AdminPass123!")

    client.get("/", follow=True)
    client.get("/", follow=True)
    client.get("/", follow=True)

    assert FinancialProfile.objects.filter(owner=user).count() == 1
