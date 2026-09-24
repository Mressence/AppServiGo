from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from technicians.models import TechnicianProfile
from .forms import RegisterForm
from .forms import ProfileForm

def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.role == "TECNICO":
                TechnicianProfile.objects.create(user=user)
                messages.success(request, "Cuenta creada. Tu perfil de técnico quedó pendiente de aprobación.")
            else:
                messages.success(request, "Cuenta creada correctamente.")
            login(request, user)
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
    logout(request)
    return redirect("home")

@login_required
def dashboard(request):
    context = {}
    if request.user.role == "TECNICO":
        context["technician"] = getattr(request.user, "technician_profile", None)
    return render(request, "accounts/dashboard.html", context)

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
            return redirect("accounts:profile")

    else:
        form = ProfileForm(instance=request.user)

    return render(
        request,
        "accounts/profile.html",
        {"form": form}
    )