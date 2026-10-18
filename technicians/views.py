from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from accounts.models import User
from .forms import TechnicianApplicationForm
from .models import TechnicianProfile


@login_required
def profile(request):
    """Compatibilidad con la URL antigua /technicians/perfil/."""
    return redirect("accounts:profile")


@login_required
def application(request):
    if request.user.role == User.Role.ADMINISTRADOR or request.user.is_staff:
        return redirect("accounts:dashboard")
    profile, _ = TechnicianProfile.objects.get_or_create(user=request.user, defaults={"professional_title": "Pendiente de completar"})
    if profile.status in (TechnicianProfile.Status.PENDIENTE, TechnicianProfile.Status.APROBADO):
        return redirect("technicians:application_status")
    if request.method == "POST":
        form = TechnicianApplicationForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.status = TechnicianProfile.Status.PENDIENTE
            application.submitted_at = timezone.now()
            application.admin_feedback = ""
            application.rejection_reason = ""
            application.save()
            messages.success(request, "Solicitud enviada. Mientras esté pendiente no podrás editarla.")
            return redirect("technicians:application_status")
    else:
        form = TechnicianApplicationForm(instance=profile)
    return render(request, "technicians/application.html", {"form": form, "application": profile})


@login_required
def application_status(request):
    application = TechnicianProfile.objects.filter(user=request.user).first()
    if application is None:
        return redirect("technicians:application")
    return render(request, "technicians/application_status.html", {"application": application})
