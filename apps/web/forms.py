from django import forms


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
