"""Account views — login, logout, register, profile."""
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView, UpdateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django import forms
from .models import User


class LoginForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña", min_length=8)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmar contraseña")

    class Meta:
        model = User
        fields = ["email", "username", "first_name", "last_name"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password_confirm"):
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned


class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = authenticate(
            self.request,
            username=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if user:
            login(self.request, user)
            next_url = self.request.GET.get("next", "dashboard:home")
            return redirect(next_url)
        form.add_error(None, "Credenciales incorrectas.")
        return self.form_invalid(form)


class LogoutView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "Sesión cerrada correctamente.")
        return redirect("accounts:login")


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        user = User.objects.create_user(
            email=form.cleaned_data["email"],
            username=form.cleaned_data["username"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            password=form.cleaned_data["password"],
        )
        login(self.request, user)
        messages.success(self.request, f"¡Bienvenido a Lexora Library, {user.first_name}!")
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        from apps.loans.models import Loan
        ctx["active_loans"] = Loan.objects.filter(user=user, status=Loan.Status.BORROWED)
        ctx["loan_history"] = Loan.objects.filter(user=user).order_by("-loan_date")[:10]
        ctx["review_count"] = user.reviews.count()
        return ctx
