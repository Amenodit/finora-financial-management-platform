"""
Field-level encryption for sensitive PII (phone numbers, dates of birth,
account numbers). This is deliberately hand-rolled and small rather than a
pulled-in third-party package, because the obvious "django-cryptography"
package doesn't support current Django, and this need is simple enough not
to justify a heavier dependency.

Encrypted values are stored as base64 ciphertext in a TextField. This is a
practical middle ground: it protects the data if the database is dumped or
read directly, without needing full disk/volume encryption to be configured
correctly everywhere. It is not a substitute for TLS in transit or for
database access controls — it's one more layer.
"""
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _fernet():
    key = settings.FIELD_ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


class EncryptedTextField(models.TextField):
    """Transparently encrypts on save, decrypts on load."""

    description = "Encrypted text field"

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        token = _fernet().encrypt(str(value).encode())
        return token.decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            # Data written before encryption was enabled, or wrong key.
            # Fail safe: surface as None rather than raising into a page render.
            return None

    def to_python(self, value):
        return value
