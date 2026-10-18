from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from accounts.models import User
from .forms import TechnicianApplicationForm
from .models import TechnicianProfile
from django.db.models import Avg, Count
from service_requests.models import ServiceRequest, TechnicianReview


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
def public_profile(request, pk):
    profile = get_object_or_404(
        TechnicianProfile.objects.select_related("user", "category"),
        pk=pk,
        status=TechnicianProfile.Status.APROBADO,
        category__active=True,
        user__is_active=True,
    )

    reviews = TechnicianReview.objects.filter(
        technician=profile.user,
        service_request__status="COMPLETADA",
    ).select_related("reviewer")

    summary = reviews.aggregate(
        average=Avg("rating"),
        total=Count("id"),
    )

    return render(
        request,
        "technicians/public_profile.html",
        {
            "profile": profile,
            "reviews": reviews,
            "average_rating": summary["average"],
            "review_count": summary["total"],
        },
    )
@login_required
def create_review(request, request_id):
    if request.method != "POST":
        return redirect("service_requests:list")

    service_request = get_object_or_404(
        ServiceRequest.objects.select_related(
            "requester",
            "assigned_technician",
        ),
        pk=request_id,
        requester=request.user,
        status=ServiceRequest.Status.COMPLETADA,
        assigned_technician__isnull=False,
    )

    # Una solicitud solo puede recibir una reseña.
    if TechnicianReview.objects.filter(
        service_request=service_request
    ).exists():
        messages.error(
            request,
            "Esta solicitud ya tiene una reseña."
        )
        return redirect(
            "service_requests:detail",
            pk=service_request.pk,
        )

    try:
        rating = int(request.POST.get("rating", ""))
    except (TypeError, ValueError):
        rating = 0

    comment = request.POST.get("comment", "").strip()

    if not 1 <= rating <= 5:
        messages.error(
            request,
            "Selecciona una calificación entre 1 y 5 estrellas."
        )
        return redirect(
            "service_requests:detail",
            pk=service_request.pk,
        )

    TechnicianReview.objects.create(
        service_request=service_request,
        technician=service_request.assigned_technician,
        reviewer=request.user,
        rating=rating,
        comment=comment,
    )

    messages.success(
        request,
        "Tu reseña se publicó correctamente."
    )

    return redirect(
        "service_requests:detail",
        pk=service_request.pk,
    )