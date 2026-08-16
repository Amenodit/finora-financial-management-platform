import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from apps.common.fields import EncryptedTextField


class UserManager(BaseUserManager):
    """Email is the login identifier — usernames add nothing for this product."""

    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model, keyed by email. Kept deliberately minimal on required
    fields per the spec ("do not unnecessarily collect sensitive information").
    Phone and date of birth are optional and encrypted at rest.
    """

    username = None
    email = models.EmailField(unique=True, db_index=True)

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    phone_number = EncryptedTextField(null=True, blank=True)
    date_of_birth = EncryptedTextField(null=True, blank=True)  # stored as ISO string, encrypted

    preferred_currency = models.CharField(max_length=3, default="INR")
    country = models.CharField(max_length=2, blank=True, default="")
    timezone = models.CharField(max_length=64, default="UTC")
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True)

    # --- MFA (TOTP) ---
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = EncryptedTextField(null=True, blank=True)
    mfa_backup_codes = models.JSONField(default=list, blank=True)  # stores salted hashes, never raw codes

    # --- Account security bookkeeping ---
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        indexes = [models.Index(fields=["email"])]

    def __str__(self):
        return self.email

    @property
    def is_locked(self):
        from django.utils import timezone

        return bool(self.locked_until and self.locked_until > timezone.now())
