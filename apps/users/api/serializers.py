from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    preferred_currency = serializers.CharField(required=False, default="INR", max_length=3)
    country = serializers.CharField(required=False, allow_blank=True, default="")
    timezone = serializers.CharField(required=False, default="UTC")

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password

        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    mfa_code = serializers.CharField(required=False, allow_blank=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "public_id", "email", "first_name", "last_name", "phone_number",
            "date_of_birth", "preferred_currency", "country", "timezone",
            "profile_image", "mfa_enabled", "date_joined",
        ]
        read_only_fields = ["public_id", "email", "mfa_enabled", "date_joined"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=10)

    def validate_new_password(self, value):
        from django.contrib.auth.password_validation import validate_password

        validate_password(value)
        return value


class MFAConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6)
