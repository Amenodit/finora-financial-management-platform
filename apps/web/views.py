from django.contrib.auth import get_user_model, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_http_methods

from apps.accounts.services import account_service
from apps.profiles.models import FinancialProfile
from apps.profiles.services.profile_service import create_default_profile
from apps.transactions.services import transaction_service
from apps.transactions.models import Transaction
from apps.users.services import auth_service
from apps.web.forms import AccountForm, LoginForm, RegisterForm, TransactionForm

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
    profile = _get_or_create_default_profile(request.user)

    context = {"profile": profile, "has_profile": True}

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
        "has_accounts": profile.accounts.exists(),
    })

    return render(request, "dashboard/index.html", context)


def _get_or_create_default_profile(user):
    """
    Every real signup gets a default profile automatically. But accounts
    created outside that flow — e.g. `createsuperuser`, or a profile that
    was deleted — would otherwise hit a dead end in the UI. Self-heal here
    instead of showing an error the user can't do anything about.
    """
    profile = FinancialProfile.objects.filter(owner=user).order_by("-is_default").first()
    if profile is None:
        profile = create_default_profile(user)
    return profile


@login_required
def transactions_list(request):
    profile = _get_or_create_default_profile(request.user)
    transactions = Transaction.objects.filter(profile=profile).select_related("account", "category")[:100]
    return render(request, "transactions/list.html", {"profile": profile, "transactions": transactions})


@login_required
def transaction_create(request):
    profile = _get_or_create_default_profile(request.user)

    if not profile.accounts.exists():
        messages.info(request, "Add an account first — transactions have to belong to one.")
        return redirect("web:account_create")

    if request.method == "POST":
        form = TransactionForm(request.POST, profile=profile)
        if form.is_valid():
            data = form.cleaned_data
            try:
                transaction_service.create_transaction(
                    profile=profile,
                    account=data["account"],
                    category=data.get("category"),
                    transaction_type=data["transaction_type"],
                    amount=data["amount"],
                    transaction_date=data["transaction_date"],
                    description=data.get("description", ""),
                    merchant=data.get("merchant", ""),
                    created_by=request.user,
                    request=request,
                )
            except transaction_service.DuplicateTransactionError:
                messages.error(
                    request,
                    "This looks identical to an existing transaction (same account, date, amount, "
                    "and description). If that's intentional, change one field slightly and resubmit.",
                )
            except DjangoValidationError as exc:
                messages.error(request, exc.messages[0] if exc.messages else "Could not save transaction.")
            else:
                messages.success(request, "Transaction added.")
                return redirect("web:transactions")
    else:
        form = TransactionForm(profile=profile)

    return render(request, "transactions/form.html", {"form": form})


@login_required
def accounts_list(request):
    profile = _get_or_create_default_profile(request.user)
    accounts = profile.accounts.all()
    return render(request, "accounts/list.html", {"profile": profile, "accounts": accounts})


@login_required
def account_create(request):
    profile = _get_or_create_default_profile(request.user)

    if request.method == "POST":
        form = AccountForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            account_service.create_account(
                profile=profile,
                name=data["name"],
                account_type=data["account_type"],
                institution=data.get("institution", ""),
                currency=data.get("currency") or profile.currency,
                opening_balance=data.get("opening_balance") or 0,
                last_four_digits=data.get("last_four_digits") or None,
                actor=request.user,
                request=request,
            )
            messages.success(request, "Account added.")
            return redirect("web:accounts")
    else:
        form = AccountForm(initial={"currency": profile.currency})

    return render(request, "accounts/form.html", {"form": form})


@login_required
def settings_view(request):
    return render(request, "settings/index.html", {})


@login_required
def coming_soon(request, section):
    return render(request, "shared/coming_soon.html", {"section": section})
