from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import TechnicianProfileForm

@login_required
def profile(request):
    if request.user.role != "TECNICO":
        return redirect("accounts:dashboard")
    profile = request.user.technician_profile
    if request.method == "POST":
        form = TechnicianProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            if profile.status == "RECHAZADO":
                profile.status = "PENDIENTE"
                profile.rejection_reason = ""
            profile.save()
            messages.success(request, "Perfil actualizado. Si corresponde, volverá a revisión.")
            return redirect("technicians:profile")
    else:
        form = TechnicianProfileForm(instance=profile)
    return render(request, "technicians/profile.html", {"form": form, "profile": profile})
