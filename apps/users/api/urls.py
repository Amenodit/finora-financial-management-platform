from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.api.views import (
    ChangePasswordView,
    LoginView,
    MeView,
    MFAConfirmView,
    MFADisableView,
    MFAEnrollView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("mfa/enroll/", MFAEnrollView.as_view(), name="mfa-enroll"),
    path("mfa/confirm/", MFAConfirmView.as_view(), name="mfa-confirm"),
    path("mfa/disable/", MFADisableView.as_view(), name="mfa-disable"),
]
