from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import TechnicianApplicationForm
from .models import TechnicianProfile

@login_required
def technician_application(request):

    if request.user.role == "TECNICO":
        return redirect("accounts:profile")

    profile, created = TechnicianProfile.objects.get_or_create(
        user=request.user
    )

    if profile.status == TechnicianProfile.Status.PENDIENTE:
        return redirect("technicians:application_status")

    if profile.status == TechnicianProfile.Status.APROBADO:
        return redirect("accounts:profile")

    if request.method == "POST":

        form = TechnicianApplicationForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():

            technician = form.save(commit=False)

            technician.user = request.user
            technician.status = TechnicianProfile.Status.PENDIENTE

            technician.save()

            return redirect(
                "technicians:application_status"
            )

    else:

        form = TechnicianApplicationForm(
            instance=profile
        )

    return render(
        request,
        "technicians/application.html",
        {"form": form}
    )
@login_required
def application_status(request):

    try:
        application = request.user.technician_profile
    except TechnicianProfile.DoesNotExist:
        return redirect("technicians:application")

    return render(
        request,
        "technicians/application_status.html",
        {
            "application": application
        }
    )