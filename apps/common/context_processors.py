from django.conf import settings


def app_meta(request):
    """Makes a few safe, non-secret settings available to every template."""
    return {
        "APP_NAME": "Finora",
        "DEFAULT_CURRENCY": settings.DEFAULT_CURRENCY,
        "SUPPORTED_CURRENCIES": settings.SUPPORTED_CURRENCIES,
    }
