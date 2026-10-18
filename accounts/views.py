from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render

from technicians.models import TechnicianProfile
from service_requests.models import ServiceRequest
from .forms import RegisterForm, ProfileForm, StyledPasswordChangeForm
from .models import User


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Tu cuenta se creó correctamente.")
            return redirect("accounts:dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("accounts:dashboard")
        messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, "accounts/login.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
    else:
        logout(request)
    return redirect("home")


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil se actualizó correctamente.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    application = getattr(request.user, "technician_profile", None)
    return render(request, "accounts/profile.html", {"form": form, "application": application})


class ServiGoPasswordChangeView(PasswordChangeView):
    form_class = StyledPasswordChangeForm
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Tu contraseña se cambió correctamente.")
        return super().form_valid(form)


@login_required
def dashboard(request):
    context = {
        "my_requests": ServiceRequest.objects.filter(requester=request.user).select_related("service_type", "assigned_technician").order_by("-created_at")[:5],
        "my_requests_count": ServiceRequest.objects.filter(requester=request.user).count(),
    }
    if request.user.role == User.Role.TECNICO:
        context["technician"] = getattr(request.user, "technician_profile", None)
        context["available_requests_count"] = ServiceRequest.objects.filter(status__in=[ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA]).exclude(requester=request.user).count()
        context["assigned_requests"] = ServiceRequest.objects.filter(assigned_technician=request.user).exclude(status=ServiceRequest.Status.COMPLETADA).order_by("-updated_at")[:5]
    if request.user.role == User.Role.ADMINISTRADOR or request.user.is_staff:
        context["pending_technicians_count"] = TechnicianProfile.objects.filter(status=TechnicianProfile.Status.PENDIENTE).count()
        context["open_requests_count"] = ServiceRequest.objects.filter(status__in=[ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA]).count()
    return render(request, "accounts/dashboard.html", context)
