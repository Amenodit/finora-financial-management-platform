from django.urls import path

from apps.web import views

app_name = "web"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("transactions/", views.transactions_list, name="transactions"),
    path("accounts/", views.accounts_list, name="accounts"),
    path("settings/", views.settings_view, name="settings"),
    path("budgets/", views.coming_soon, {"section": "Budgets"}, name="budgets"),
    path("savings/", views.coming_soon, {"section": "Savings Goals"}, name="savings"),
    path("statements/", views.coming_soon, {"section": "Bank Statements"}, name="statements"),
    path("reports/", views.coming_soon, {"section": "Reports"}, name="reports"),
    path("family/", views.coming_soon, {"section": "Family"}, name="family"),
    path("analytics/", views.coming_soon, {"section": "Analytics"}, name="analytics"),
]
