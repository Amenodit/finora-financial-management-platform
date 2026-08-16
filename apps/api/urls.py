from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.api.views import AccountViewSet
from apps.api.views import HealthCheckView
from apps.categories.api.views import CategoryViewSet
from apps.profiles.api.views import FinancialProfileViewSet
from apps.transactions.api.views import TransactionViewSet

router = DefaultRouter()
router.register("profiles", FinancialProfileViewSet, basename="profile")
router.register("accounts", AccountViewSet, basename="account")
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("auth/", include("apps.users.api.urls")),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("", include(router.urls)),
]
