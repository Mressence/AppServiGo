from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render

from technicians.models import TechnicianProfile
from .forms import RegisterForm, ProfileForm, StyledPasswordChangeForm
from .models import User


def get_login_destination(user):
    """
    Decide a qué pantalla dirigir al usuario después de entrar.
    """

    # Administradores: página principal.
    if user.is_superuser or user.is_staff:
        return "home"

    # Técnicos: solicitudes si están aprobados;
    # perfil si aún están en revisión.
    if user.role == User.Role.TECNICO:
        profile = getattr(user, "technician_profile", None)

        if profile and profile.status == TechnicianProfile.Status.APROBADO:
            return "service_requests:list"

        return "accounts:profile"

    # Clientes: catálogo de servicios.
    return "catalog:catalog"


def register(request):
    if request.user.is_authenticated:
        return redirect(get_login_destination(request.user))

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                "Tu cuenta se creó correctamente."
            )

            return redirect(get_login_destination(user))
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form}
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_login_destination(request.user))

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect(get_login_destination(user))

        messages.error(
            request,
            "Usuario o contraseña incorrectos."
        )

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Tu perfil se actualizó correctamente."
            )

            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    application = getattr(
        request.user,
        "technician_profile",
        None
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "application": application
        }
    )


class ServiGoPasswordChangeView(PasswordChangeView):
    form_class = StyledPasswordChangeForm
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Tu contraseña se cambió correctamente."
        )

        return super().form_valid(form)
