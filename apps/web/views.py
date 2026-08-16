from django.contrib.auth import get_user_model, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_http_methods

from apps.profiles.models import FinancialProfile
from apps.transactions.services import transaction_service
from apps.transactions.models import Transaction
from apps.users.services import auth_service
from apps.web.forms import LoginForm, RegisterForm

User = get_user_model()


class RegisterView(View):
    template_name = "auth/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("web:dashboard")
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        try:
            user = auth_service.register_user(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
            )
        except DjangoValidationError as exc:
            form.add_error("email", exc.messages[0] if exc.messages else "Registration failed.")
            return render(request, self.template_name, {"form": form})

        django_login(request, user)
        messages.success(request, "Welcome! Your account and Personal profile are ready.")
        return redirect("web:dashboard")


class LoginView(View):
    template_name = "auth/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("web:dashboard")
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        data = form.cleaned_data
        try:
            user = auth_service.authenticate_credentials(
                email=data["email"], password=data["password"],
                mfa_code=data.get("mfa_code") or None, request=request,
            )
        except auth_service.MFARequiredError:
            form.fields["mfa_code"].required = True
            messages.info(request, "Enter your 6-digit authenticator code to continue.")
            return render(request, self.template_name, {"form": form, "mfa_required": True})
        except auth_service.AccountLockedError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {"form": form})
        except auth_service.AuthenticationError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {"form": form})

        django_login(request, user)
        return redirect("web:dashboard")


@require_http_methods(["POST"])
def logout_view(request):
    django_logout(request)
    return redirect("web:login")


@login_required
def dashboard(request):
    profile = FinancialProfile.objects.filter(owner=request.user).order_by("-is_default").first()

    context = {"profile": profile, "has_profile": profile is not None}

    if profile:
        income = transaction_service.total_income(profile)
        expenses = transaction_service.total_expenses(profile)
        context.update({
            "income": income,
            "expenses": expenses,
            "savings": income - expenses,
            "savings_rate": transaction_service.savings_rate(profile),
            "category_spending": list(transaction_service.category_spending(profile))[:6],
            "recent_transactions": Transaction.objects.filter(profile=profile).select_related(
                "account", "category"
            )[:8],
        })

    return render(request, "dashboard/index.html", context)


@login_required
def transactions_list(request):
    profile = FinancialProfile.objects.filter(owner=request.user).order_by("-is_default").first()
    transactions = Transaction.objects.none()
    if profile:
        transactions = Transaction.objects.filter(profile=profile).select_related("account", "category")[:100]
    return render(request, "transactions/list.html", {"profile": profile, "transactions": transactions})


@login_required
def accounts_list(request):
    profile = FinancialProfile.objects.filter(owner=request.user).order_by("-is_default").first()
    accounts = profile.accounts.all() if profile else []
    return render(request, "accounts/list.html", {"profile": profile, "accounts": accounts})


@login_required
def settings_view(request):
    return render(request, "settings/index.html", {})


@login_required
def coming_soon(request, section):
    return render(request, "shared/coming_soon.html", {"section": section})
