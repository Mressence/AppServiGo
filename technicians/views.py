from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from service_requests.models import ServiceRequest, TechnicianReview, Appointment
from .forms import TechnicianApplicationForm, TechnicianAvailabilityForm, AvailabilityExceptionForm
from .models import TechnicianProfile, TechnicianAvailability, AvailabilityException
from .services import available_start_times


def profile(request):
    return redirect("accounts:profile")


@login_required
def application(request):
    if request.user.role == User.Role.ADMINISTRADOR or request.user.is_staff:
        return redirect("home")
    profile, _ = TechnicianProfile.objects.get_or_create(
        user=request.user, defaults={"professional_title": "Pendiente de completar"}
    )
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
            messages.success(request, "Solicitud enviada para revisión.")
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
        pk=pk, status=TechnicianProfile.Status.APROBADO,
        category__active=True, user__is_active=True,
    )
    reviews = TechnicianReview.objects.filter(
        technician=profile.user, service_request__status=ServiceRequest.Status.COMPLETADA,
    ).select_related("reviewer")
    summary = reviews.aggregate(average=Avg("rating"), total=Count("id"))
    return render(request, "technicians/public_profile.html", {
        "profile": profile, "reviews": reviews,
        "average_rating": summary["average"], "review_count": summary["total"],
    })


@login_required
def create_review(request, request_id):
    if request.method != "POST":
        return redirect("service_requests:list")
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related("requester", "assigned_technician"),
        pk=request_id, requester=request.user,
        status=ServiceRequest.Status.COMPLETADA, assigned_technician__isnull=False,
    )
    if TechnicianReview.objects.filter(service_request=service_request).exists():
        messages.error(request, "Esta solicitud ya tiene una reseña.")
        return redirect("service_requests:detail", pk=service_request.pk)
    try:
        rating = int(request.POST.get("rating", ""))
    except (TypeError, ValueError):
        rating = 0
    if not 1 <= rating <= 5:
        messages.error(request, "Selecciona una calificación entre 1 y 5 estrellas.")
        return redirect("service_requests:detail", pk=service_request.pk)
    TechnicianReview.objects.create(
        service_request=service_request, technician=service_request.assigned_technician,
        reviewer=request.user, rating=rating,
        comment=request.POST.get("comment", "").strip(),
    )
    messages.success(request, "Tu reseña se publicó correctamente.")
    return redirect("service_requests:detail", pk=service_request.pk)


@login_required
def availability_manage(request):
    profile = getattr(request.user, "technician_profile", None)
    if not profile or profile.status != TechnicianProfile.Status.APROBADO:
        raise PermissionDenied("Solo técnicos aprobados pueden configurar su disponibilidad.")
    if request.method == "POST":
        form = TechnicianAvailabilityForm(request.POST, technician=request.user)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.technician = request.user
            slot.save()
            messages.success(request, "Horario guardado correctamente.")
            return redirect("technicians:availability")
    else:
        form = TechnicianAvailabilityForm(technician=request.user)
    slots = TechnicianAvailability.objects.filter(technician=request.user)
    exceptions = AvailabilityException.objects.filter(technician=request.user)
    return render(request, "technicians/availability.html", {
        "form": form, "slots": slots, "exceptions": exceptions,
        "exception_form": AvailabilityExceptionForm(),
    })


@login_required
def availability_delete(request, pk):
    if request.method != "POST":
        raise PermissionDenied
    slot = get_object_or_404(TechnicianAvailability, pk=pk, technician=request.user)
    slot.delete()
    messages.success(request, "Horario eliminado.")
    return redirect("technicians:availability")


@login_required
def availability_exception_create(request):
    profile = getattr(request.user, "technician_profile", None)
    if not profile or profile.status != TechnicianProfile.Status.APROBADO or request.method != "POST":
        raise PermissionDenied
    form = AvailabilityExceptionForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.technician = request.user
        obj.save()
        messages.success(request, "Bloqueo de disponibilidad registrado.")
    else:
        messages.error(request, "No se pudo guardar el bloqueo: " + "; ".join(form.errors.get("__all__", [])))
    return redirect("technicians:availability")


@login_required
def availability_exception_delete(request, pk):
    if request.method != "POST":
        raise PermissionDenied
    obj = get_object_or_404(AvailabilityException, pk=pk, technician=request.user)
    obj.delete()
    messages.success(request, "Bloqueo eliminado.")
    return redirect("technicians:availability")


@login_required
def technician_calendar(request):
    if request.user.is_staff or request.user.role == User.Role.ADMINISTRADOR:
        appointments = Appointment.objects.select_related("service_request", "technician", "service_request__requester")
    elif request.user.role == User.Role.TECNICO:
        appointments = Appointment.objects.filter(technician=request.user).select_related("service_request", "service_request__requester")
    else:
        appointments = Appointment.objects.filter(service_request__requester=request.user).select_related("service_request", "technician")
    return render(request, "technicians/calendar.html", {"appointments": appointments, "public_technician": None})


@login_required
@login_required
def public_technician_calendar(request, pk):
    profile = get_object_or_404(
        TechnicianProfile.objects.select_related("user", "category"),
        pk=pk, status=TechnicianProfile.Status.APROBADO,
        category__active=True, user__is_active=True,
    )
    selected_request = None
    request_id = request.GET.get("solicitud")
    if request_id:
        selected_request = get_object_or_404(
            ServiceRequest,
            pk=request_id,
            requester=request.user,
            assigned_technician=profile.user,
            status__in=[ServiceRequest.Status.ACEPTADA, ServiceRequest.Status.PROGRAMADA],
        )
        if Appointment.objects.filter(service_request=selected_request).exists():
            return redirect("service_requests:appointment_detail",
                            pk=selected_request.appointment.pk)
    return render(request, "technicians/calendar.html", {
        "appointments": Appointment.objects.filter(
            technician=profile.user,
            status__in=[Appointment.Status.PROGRAMADA, Appointment.Status.CONFIRMADA],
        ),
        "public_technician": profile,
        "selected_request": selected_request,
    })


@login_required
def availability_slots(request):
    technician_id = request.GET.get("tecnico")
    date_value = request.GET.get("fecha", "")
    profile = get_object_or_404(
        TechnicianProfile.objects.select_related("user"),
        user_id=technician_id,
        status=TechnicianProfile.Status.APROBADO,
        category__active=True,
        user__is_active=True,
    )
    try:
        selected_day = datetime.strptime(date_value, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"slots": []})
    slots = available_start_times(profile.user, selected_day)
    return JsonResponse({"slots": [{"value": value, "label": label} for value, label in slots]})


@login_required
def calendar_events(request):
    technician_profile_id = request.GET.get("tecnico")
    if technician_profile_id:
        profile = get_object_or_404(
            TechnicianProfile.objects.select_related("user"),
            pk=technician_profile_id, status=TechnicianProfile.Status.APROBADO,
            category__active=True, user__is_active=True,
        )
        technician = profile.user
        selected_request = None
        selected_request_id = request.GET.get("solicitud")
        if selected_request_id:
            selected_request = get_object_or_404(
                ServiceRequest,
                pk=selected_request_id,
                requester=request.user,
                assigned_technician=technician,
                status__in=[ServiceRequest.Status.ACEPTADA, ServiceRequest.Status.PROGRAMADA],
            )
        try:
            range_start = datetime.fromisoformat(request.GET.get("start", "").replace("Z", "+00:00")).date()
            range_end = datetime.fromisoformat(request.GET.get("end", "").replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            today = timezone.localdate()
            range_start, range_end = today, today + timedelta(days=45)
        events = []
        day = range_start
        while day < range_end:
            # El calendario marca el día como disponible solo si queda al menos un bloque libre real.
            if available_start_times(
                technician, day, duration_minutes=60, step_minutes=30,
                exclude_request=selected_request,
            ):
                events.append({"title": "Disponible", "start": day.isoformat(),
                               "end": (day + timedelta(days=1)).isoformat(), "allDay": True,
                               "display": "background", "backgroundColor": "#bbf7d0", "borderColor": "#86efac"})
            day += timedelta(days=1)
        busy = Appointment.objects.filter(
            technician=technician,
            status__in=[Appointment.Status.PROGRAMADA, Appointment.Status.CONFIRMADA],
            start_at__lt=timezone.make_aware(datetime.combine(range_end, datetime.min.time()), timezone.get_current_timezone()),
            end_at__gt=timezone.make_aware(datetime.combine(range_start, datetime.min.time()), timezone.get_current_timezone()),
        )
        for item in busy:
            events.append({"title": "Horario reservado", "start": item.start_at.isoformat(), "end": item.end_at.isoformat(),
                           "backgroundColor": "#fecaca", "borderColor": "#f87171"})
        # Show provisional time selections too, without exposing client details.
        provisional = ServiceRequest.objects.filter(
            assigned_technician=technician,
            status__in=[
                ServiceRequest.Status.PENDIENTE,
                ServiceRequest.Status.COTIZADA,
                ServiceRequest.Status.ACEPTADA,
                ServiceRequest.Status.PROGRAMADA,
                ServiceRequest.Status.EN_EJECUCION,
            ],
            requested_start_at__isnull=False,
            requested_start_at__lt=timezone.make_aware(
                datetime.combine(range_end, datetime.min.time()),
                timezone.get_current_timezone(),
            ),
            requested_end_at__gt=timezone.make_aware(
                datetime.combine(range_start, datetime.min.time()),
                timezone.get_current_timezone(),
            ),
            appointment__isnull=True,
        )
        if selected_request is not None:
            provisional = provisional.exclude(pk=selected_request.pk)
        for item in provisional:
            events.append({
                "title": "Horario solicitado",
                "start": item.requested_start_at.isoformat(),
                "end": item.requested_end_at.isoformat(),
                "backgroundColor": "#fed7aa",
                "borderColor": "#fb923c",
            })
        return JsonResponse(events, safe=False)

    if request.user.is_staff or request.user.role == User.Role.ADMINISTRADOR:
        qs = Appointment.objects.select_related("service_request", "technician", "service_request__requester")
    elif request.user.role == User.Role.TECNICO:
        qs = Appointment.objects.filter(technician=request.user).select_related("service_request", "service_request__requester")
    else:
        qs = Appointment.objects.filter(service_request__requester=request.user).select_related("service_request", "technician")
    events = []
    if request.user.role == User.Role.TECNICO:
        provisional_qs = ServiceRequest.objects.filter(
            assigned_technician=request.user,
            status__in=[
                ServiceRequest.Status.PENDIENTE,
                ServiceRequest.Status.COTIZADA,
                ServiceRequest.Status.ACEPTADA,
            ],
            requested_start_at__isnull=False,
            appointment__isnull=True,
        ).select_related("service_type", "requester")
        for pending in provisional_qs:
            events.append({
                "id": f"request-{pending.pk}",
                "title": f"Horario solicitado · {pending.service_type.name}",
                "start": pending.requested_start_at.isoformat(),
                "end": pending.requested_end_at.isoformat(),
                "url": f"/solicitudes/{pending.pk}/",
                "backgroundColor": "#fed7aa",
                "borderColor": "#fb923c",
            })
    elif not (request.user.is_staff or request.user.role == User.Role.ADMINISTRADOR):
        provisional_qs = ServiceRequest.objects.filter(
            requester=request.user,
            status__in=[
                ServiceRequest.Status.PENDIENTE,
                ServiceRequest.Status.COTIZADA,
                ServiceRequest.Status.ACEPTADA,
            ],
            requested_start_at__isnull=False,
            appointment__isnull=True,
        ).select_related("service_type")
        for pending in provisional_qs:
            events.append({
                "id": f"request-{pending.pk}",
                "title": f"{pending.get_status_display()} · {pending.service_type.name}",
                "start": pending.requested_start_at.isoformat(),
                "end": pending.requested_end_at.isoformat(),
                "url": f"/solicitudes/{pending.pk}/",
                "backgroundColor": "#dbeafe",
                "borderColor": "#60a5fa",
            })
    for item in qs:
        if request.user.role == User.Role.TECNICO:
            title = f"{item.service_request.service_type.name} · {item.service_request.requester.get_full_name() or item.service_request.requester.username}"
        else:
            title = f"{item.service_request.service_type.name} · {item.get_status_display()}"
        events.append({"id": item.pk, "title": title, "start": item.start_at.isoformat(),
                       "end": item.end_at.isoformat(), "url": f"/solicitudes/cita/{item.pk}/"})
    return JsonResponse(events, safe=False)
