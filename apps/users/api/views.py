from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.api.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    MFAConfirmSerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.users.services import auth_service

User = get_user_model()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = auth_service.register_user(**serializer.validated_data)
        except DjangoValidationError as exc:
            raise ValidationError({"email": exc.messages})

        return Response(
            {"user": UserSerializer(user).data, "tokens": _tokens_for_user(user)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = auth_service.authenticate_credentials(
                email=data["email"],
                password=data["password"],
                mfa_code=data.get("mfa_code") or None,
                request=request,
            )
        except auth_service.MFARequiredError:
            return Response({"mfa_required": True}, status=status.HTTP_401_UNAUTHORIZED)
        except auth_service.AccountLockedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_423_LOCKED)
        except auth_service.AuthenticationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"user": UserSerializer(user).data, "tokens": _tokens_for_user(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not check_password(serializer.validated_data["old_password"], user.password):
            raise ValidationError({"old_password": "Incorrect current password."})
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated."})


class MFAEnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        secret, uri = auth_service.start_mfa_enrollment(request.user)
        return Response({"secret": secret, "provisioning_uri": uri})


class MFAConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MFAConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            backup_codes = auth_service.confirm_mfa_enrollment(request.user, serializer.validated_data["code"])
        except DjangoValidationError as exc:
            raise ValidationError({"code": exc.messages})
        return Response({"detail": "MFA enabled.", "backup_codes": backup_codes})


class MFADisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_service.disable_mfa(request.user)
        return Response({"detail": "MFA disabled."})
