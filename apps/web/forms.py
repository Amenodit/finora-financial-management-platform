from django import forms

from apps.accounts.models import Account
from apps.transactions.models import Transaction

TEXT_INPUT_CLASS = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500"
)


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500",
        "placeholder": "you@example.com",
        "autocomplete": "email",
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500",
        "placeholder": "••••••••",
        "autocomplete": "current-password",
    }))
    mfa_code = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500",
        "placeholder": "6-digit code",
    }))


class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        "class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500",
    }))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={
        "class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500",
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500",
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500",
    }))

    def clean_password(self):
        from django.contrib.auth.password_validation import validate_password

        password = self.cleaned_data["password"]
        validate_password(password)
        return password


class AccountForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASS, "placeholder": "e.g. HDFC Savings"}),
    )
    account_type = forms.ChoiceField(
        choices=Account.TYPE_CHOICES,
        widget=forms.Select(attrs={"class": TEXT_INPUT_CLASS}),
    )
    institution = forms.CharField(
        required=False, max_length=100,
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASS, "placeholder": "e.g. HDFC Bank"}),
    )
    currency = forms.CharField(
        max_length=3, initial="INR",
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASS, "placeholder": "INR"}),
    )
    opening_balance = forms.DecimalField(
        required=False, initial=0, max_digits=14, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={"class": TEXT_INPUT_CLASS, "step": "0.01", "placeholder": "0.00"}),
    )
    last_four_digits = forms.RegexField(
        regex=r"^\d{4}$", required=False,
        error_messages={"invalid": "Enter exactly 4 digits, or leave blank."},
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASS, "placeholder": "1234 (optional)", "maxlength": "4"}),
    )


class TransactionForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        widget=forms.Select(attrs={"class": TEXT_INPUT_CLASS}),
    )
    category = forms.ModelChoiceField(
        queryset=None, required=False,
        widget=forms.Select(attrs={"class": TEXT_INPUT_CLASS}),
    )
    transaction_type = forms.ChoiceField(
        choices=Transaction.TYPE_CHOICES,
        widget=forms.Select(attrs={"class": TEXT_INPUT_CLASS}),
    )
    amount = forms.DecimalField(
        max_digits=14, decimal_places=2, min_value=0.01,
        widget=forms.NumberInput(attrs={"class": TEXT_INPUT_CLASS, "step": "0.01", "placeholder": "0.00"}),
    )
    transaction_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": TEXT_INPUT_CLASS, "type": "date"}),
    )
    description = forms.CharField(
        required=False, max_length=500,
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASS, "placeholder": "e.g. Grocery run"}),
    )
    merchant = forms.CharField(
        required=False, max_length=200,
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASS, "placeholder": "e.g. BigBasket (optional)"}),
    )

    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        from django.db.models import Q

        from apps.categories.models import Category

        if profile is not None:
            self.fields["account"].queryset = profile.accounts.all()
            self.fields["category"].queryset = Category.objects.filter(
                Q(owner=profile.owner) | Q(owner__isnull=True)
            )
        else:
            self.fields["category"].queryset = Category.objects.none()
