from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from catalog.models import ServiceType
from technicians.models import TechnicianProfile
from technicians.services import available_start_times
from notifications.services import notify
from .forms import ServiceRequestForm, QuotationForm, AppointmentForm, CancellationForm
from .models import ServiceRequest, RequestAttachment, Quotation, Appointment, ServiceHistory, validate_attachment
from .services import (
    create_quotation, accept_quotation, transition_request,
    create_appointment, reschedule_appointment, cancel_appointment,
    finish_appointment, confirm_appointment,
)


def _is_admin(user):
    return user.is_staff or user.role == User.Role.ADMINISTRADOR


def _is_approved_technician(user):
    profile = getattr(user, "technician_profile", None)
    return bool(user.role == User.Role.TECNICO and profile and profile.status == TechnicianProfile.Status.APROBADO)


@login_required
def request_list(request):
    if _is_admin(request.user):
        requests = ServiceRequest.objects.select_related("requester", "service_type", "assigned_technician")
    elif _is_approved_technician(request.user):
        # Privacidad: solo solicitudes asignadas expresamente a este técnico.
        requests = ServiceRequest.objects.filter(assigned_technician=request.user).select_related(
            "requester", "service_type", "assigned_technician"
        )
    else:
        requests = ServiceRequest.objects.filter(requester=request.user).select_related(
            "service_type", "assigned_technician"
        )
    return render(request, "service_requests/list.html", {"requests": requests})


@login_required
@transaction.atomic
def request_create(request):
    technician_id = request.GET.get("tecnico") or request.POST.get("technician")
    initial_technician = User.objects.filter(
        pk=technician_id, role=User.Role.TECNICO,
        technician_profile__status=TechnicianProfile.Status.APROBADO,
        technician_profile__category__active=True, is_active=True,
    ).first() if technician_id else None
    service_id = request.GET.get("service") or request.POST.get("service_type")
    initial_service = ServiceType.objects.filter(pk=service_id, active=True, category__active=True).first() if service_id else None
    date_value = request.GET.get("fecha") or request.POST.get("preferred_date") or ""
    selected_day = None
    if date_value:
        try:
            selected_day = datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            selected_day = None

    if request.method == "POST":
        form = ServiceRequestForm(request.POST, initial_technician=initial_technician, initial_service=initial_service)
    else:
        form = ServiceRequestForm(
            initial_technician=initial_technician,
            initial_service=initial_service,
            initial={"preferred_date": selected_day} if selected_day else None,
        )

    slots = available_start_times(initial_technician, selected_day) if initial_technician and selected_day else []
    if request.method == "POST" and form.is_valid():
        files = request.FILES.getlist("attachments")
        try:
            for uploaded in files:
                validate_attachment(uploaded)
            technician = form.cleaned_data["technician"]
            # Serialize bookings for this technician on databases supporting row locks.
            User.objects.select_for_update().get(pk=technician.pk)
            service_request = form.save(commit=False)
            service_request.requester = request.user
            service_request.assigned_technician = technician
            chosen_time = request.POST.get("requested_time", "").strip()
            if selected_day and chosen_time:
                valid_values = {value for value, _label in available_start_times(technician, selected_day)}
                if chosen_time not in valid_values:
                    raise ValidationError("Ese horario dejó de estar disponible. Actualiza el calendario y elige otro.")
                start_naive = datetime.combine(selected_day, datetime.strptime(chosen_time, "%H:%M").time())
                service_request.requested_start_at = timezone.make_aware(start_naive, timezone.get_current_timezone())
                service_request.requested_end_at = service_request.requested_start_at + timedelta(minutes=60)
                service_request.preferred_date = selected_day
            elif selected_day:
                raise ValidationError("Selecciona una hora disponible para continuar.")
            service_request.save()
            ServiceHistory.objects.create(
                service_request=service_request, actor=request.user,
                action="Solicitud creada y asignada",
                new_value=service_request.status,
                description=f"Solicitud enviada exclusivamente a {technician.get_full_name() or technician.username}.",
            )
            for uploaded in files:
                RequestAttachment.objects.create(service_request=service_request, file=uploaded, uploaded_by=request.user)
            notify(
                technician, "Nueva solicitud asignada",
                f"{request.user.get_full_name() or request.user.username} te seleccionó para el servicio {service_request.service_type.name}. Revisa la solicitud y envía tu cotización.",
                "REQUEST", f"/solicitudes/{service_request.pk}/",
            )
            messages.success(request, "Solicitud enviada exclusivamente al técnico seleccionado. Cuando envíe su cotización recibirás una notificación.")
            return redirect("service_requests:detail", pk=service_request.pk)
        except ValidationError as exc:
            form.add_error(None, getattr(exc, "message", str(exc)))

    return render(request, "service_requests/create.html", {
        "form": form, "selected_technician": initial_technician,
        "selected_day": selected_day, "available_slots": slots,
        "calendar_flow": bool(initial_technician and selected_day),
    })


@login_required
def request_detail(request, pk):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related("requester", "service_type", "assigned_technician")
        .prefetch_related("attachments", "quotations__technician", "history__actor"), pk=pk
    )
    is_owner = service_request.requester_id == request.user.pk
    is_assigned = service_request.assigned_technician_id == request.user.pk
    is_admin = _is_admin(request.user)
    is_tech = _is_approved_technician(request.user)
    if not (is_owner or is_assigned or is_admin):
        raise PermissionDenied("No tienes permiso para ver esta solicitud.")

    quotations = service_request.quotations.all()
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add_attachments":
                if not (is_owner or is_assigned or is_admin):
                    raise PermissionDenied("No tienes permiso para adjuntar evidencias.")
                if service_request.status in (ServiceRequest.Status.COMPLETADA, ServiceRequest.Status.CANCELADA):
                    raise ValidationError("No se pueden adjuntar evidencias a una solicitud cerrada.")
                files = request.FILES.getlist("attachments")
                if not files:
                    raise ValidationError("Selecciona al menos un archivo.")
                for uploaded in files:
                    validate_attachment(uploaded)
                for uploaded in files:
                    RequestAttachment.objects.create(service_request=service_request, file=uploaded, uploaded_by=request.user)
                messages.success(request, "Evidencias adjuntadas correctamente.")
            elif action == "cancel":
                transition_request(
                    request_obj=service_request, actor=request.user,
                    target_status=ServiceRequest.Status.CANCELADA,
                    cancellation_reason=request.POST.get("reason", "").strip(),
                )
                messages.success(request, "La solicitud fue cancelada.")
            elif action == "accept_quote":
                if not is_owner:
                    raise PermissionDenied("Solo el cliente propietario puede aceptar la cotización.")
                quote = get_object_or_404(Quotation, pk=request.POST.get("quotation_id"), service_request=service_request)
                accept_quotation(quotation=quote, requester=request.user)
                messages.success(request, "Cotización aceptada. Se notificó al técnico.")
            elif action == "transition":
                target = request.POST.get("target_status")
                valid_targets = {value for value, _label in ServiceRequest.Status.choices}
                if target not in valid_targets:
                    raise ValidationError("Estado no válido.")
                transition_request(request_obj=service_request, actor=request.user, target_status=target)
                messages.success(request, "El estado del servicio se actualizó.")
            elif action == "assign_technician" and is_admin:
                technician = get_object_or_404(
                    User, pk=request.POST.get("technician_id"), role=User.Role.TECNICO,
                    technician_profile__status=TechnicianProfile.Status.APROBADO,
                )
                if service_request.status not in (ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA):
                    raise ValidationError("No se puede cambiar el técnico después de aceptar la cotización.")
                old = service_request.assigned_technician
                previous_label = old.get_full_name() or old.username if old else "Sin asignar"
                service_request.assigned_technician = technician
                service_request.quotations.exclude(technician=technician).delete()
                service_request.quotations.filter(technician=technician).delete()
                service_request.status = ServiceRequest.Status.PENDIENTE
                service_request.save(update_fields=["assigned_technician", "status", "updated_at"])
                ServiceHistory.objects.create(
                    service_request=service_request, actor=request.user,
                    action="Técnico reasignado", previous_value=previous_label,
                    new_value=technician.get_full_name() or technician.username,
                )
                notify(technician, "Nueva solicitud asignada", f"Se te asignó la solicitud #{service_request.pk}.", "REQUEST", f"/solicitudes/{service_request.pk}/")
                if old and old.pk != technician.pk:
                    notify(old, "Solicitud reasignada", f"La solicitud #{service_request.pk} fue reasignada a otro técnico.", "REQUEST", f"/solicitudes/{service_request.pk}/")
                messages.success(request, "Técnico asignado correctamente.")
            else:
                raise PermissionDenied("Acción no permitida.")
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, getattr(exc, "message", str(exc)))
        return redirect("service_requests:detail", pk=pk)

    approved_technicians = User.objects.filter(
        role=User.Role.TECNICO, is_active=True,
        technician_profile__status=TechnicianProfile.Status.APROBADO,
        technician_profile__category_id=service_request.service_type.category_id,
    ).order_by("first_name", "username") if is_admin else User.objects.none()
    appointment = getattr(service_request, "appointment", None)
    return render(request, "service_requests/detail.html", {
        "service_request": service_request, "quotations": quotations,
        "is_owner": is_owner, "is_assigned": is_assigned, "is_admin": is_admin,
        "is_approved_technician": is_tech, "appointment": appointment,
        "approved_technicians": approved_technicians,
        "history": service_request.history.all(),
    })


@login_required
def quotation_create(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if not _is_approved_technician(request.user):
        raise PermissionDenied("Solo los técnicos aprobados pueden enviar cotizaciones.")
    if service_request.assigned_technician_id != request.user.pk:
        raise PermissionDenied("Esta solicitud no está asignada a tu cuenta.")
    if service_request.status not in (ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA):
        messages.error(request, "Esta solicitud ya no acepta cotizaciones.")
        return redirect("service_requests:detail", pk=pk)
    if request.method == "POST":
        form = QuotationForm(request.POST)
        if form.is_valid():
            try:
                quote, created = create_quotation(
                    request_obj=service_request, technician=request.user,
                    amount=form.cleaned_data["amount"], details=form.cleaned_data["details"],
                    estimated_days=form.cleaned_data["estimated_days"],
                )
            except (PermissionDenied, ValidationError) as exc:
                form.add_error(None, getattr(exc, "message", str(exc)))
            else:
                messages.success(request, "Cotización enviada al cliente." if created else "Tu cotización fue actualizada.")
                return redirect("service_requests:detail", pk=pk)
    else:
        form = QuotationForm(instance=service_request.quotations.filter(technician=request.user).first())
    return render(request, "service_requests/quotation_form.html", {"form": form, "service_request": service_request})


@login_required
def appointment_create(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if service_request.requester_id != request.user.pk and not _is_admin(request.user):
        raise PermissionDenied
    if service_request.status not in (ServiceRequest.Status.ACEPTADA, ServiceRequest.Status.PROGRAMADA):
        messages.error(request, "Primero debes aceptar una cotización.")
        return redirect("service_requests:detail", pk=pk)
    if hasattr(service_request, "appointment"):
        return redirect("service_requests:appointment_detail", pk=service_request.appointment.pk)
    selected_day = None
    date_value = request.POST.get("fecha") or request.GET.get("fecha") or ""
    if date_value:
        try:
            selected_day = datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            selected_day = None
    slots = available_start_times(
        service_request.assigned_technician,
        selected_day,
        exclude_request=service_request,
    ) if selected_day else []

    if request.method == "POST" and selected_day:
        form = AppointmentForm()
        chosen_time = request.POST.get("requested_time", "").strip()
        valid_values = {value for value, _label in slots}
        if chosen_time not in valid_values:
            form.add_error(None, "Ese horario ya no está disponible. Actualiza el calendario y selecciona otro.")
        else:
            start_time = datetime.strptime(chosen_time, "%H:%M").time()
            start_at = timezone.make_aware(
                datetime.combine(selected_day, start_time),
                timezone.get_current_timezone(),
            )
            end_at = start_at + timedelta(minutes=60)
            try:
                appointment = create_appointment(
                    request_obj=service_request, actor=request.user,
                    start_at=start_at, end_at=end_at,
                    notes=request.POST.get("notes", "").strip(),
                )
            except (PermissionDenied, ValidationError) as exc:
                form.add_error(None, getattr(exc, "message", str(exc)))
            else:
                messages.success(request, "Cita programada correctamente desde el calendario.")
                return redirect("service_requests:appointment_detail", pk=appointment.pk)
    elif request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                appointment = create_appointment(
                    request_obj=service_request, actor=request.user,
                    start_at=form.cleaned_data["start_at"], end_at=form.cleaned_data["end_at"],
                    notes=form.cleaned_data["notes"],
                )
            except (PermissionDenied, ValidationError) as exc:
                form.add_error(None, getattr(exc, "message", str(exc)))
            else:
                messages.success(request, "Cita programada correctamente.")
                return redirect("service_requests:appointment_detail", pk=appointment.pk)
    else:
        form = AppointmentForm()
    return render(request, "service_requests/appointment_form.html", {
        "form": form, "service_request": service_request, "mode": "Programar",
        "selected_day": selected_day, "available_slots": slots,
        "calendar_flow": bool(selected_day),
    })


@login_required
def appointment_list(request):
    if _is_admin(request.user):
        appointments = Appointment.objects.select_related("service_request", "technician", "service_request__requester")
    elif _is_approved_technician(request.user):
        appointments = Appointment.objects.filter(technician=request.user).select_related("service_request", "service_request__requester")
    else:
        appointments = Appointment.objects.filter(service_request__requester=request.user).select_related("service_request", "technician")
    return render(request, "service_requests/appointment_list.html", {"appointments": appointments})


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment.objects.select_related("service_request", "technician", "service_request__requester"), pk=pk)
    if not (_is_admin(request.user) or appointment.technician_id == request.user.pk or appointment.service_request.requester_id == request.user.pk):
        raise PermissionDenied
    return render(request, "service_requests/appointment_detail.html", {"appointment": appointment})


@login_required
def appointment_reschedule(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if not (_is_admin(request.user) or appointment.technician_id == request.user.pk or appointment.service_request.requester_id == request.user.pk):
        raise PermissionDenied
    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            try:
                updated = reschedule_appointment(appointment=appointment, actor=request.user,
                    start_at=form.cleaned_data["start_at"], end_at=form.cleaned_data["end_at"], notes=form.cleaned_data["notes"])
            except (PermissionDenied, ValidationError) as exc:
                form.add_error(None, getattr(exc, "message", str(exc)))
            else:
                messages.success(request, "Cita reprogramada.")
                return redirect("service_requests:appointment_detail", pk=updated.pk)
    else:
        form = AppointmentForm(instance=appointment)
    return render(request, "service_requests/appointment_form.html", {"form": form, "service_request": appointment.service_request, "mode": "Reprogramar"})


@login_required
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if not (_is_admin(request.user) or appointment.technician_id == request.user.pk or appointment.service_request.requester_id == request.user.pk):
        raise PermissionDenied
    if request.method == "POST":
        form = CancellationForm(request.POST)
        if form.is_valid():
            try:
                cancel_appointment(appointment=appointment, actor=request.user, reason=form.cleaned_data["reason"])
            except (PermissionDenied, ValidationError) as exc:
                form.add_error(None, getattr(exc, "message", str(exc)))
            else:
                messages.success(request, "Cita cancelada y participantes notificados.")
                return redirect("service_requests:detail", pk=appointment.service_request_id)
    else:
        form = CancellationForm()
    return render(request, "service_requests/cancellation_form.html", {"form": form, "appointment": appointment})


@login_required
def appointment_finish(request, pk):
    if request.method != "POST":
        raise PermissionDenied
    appointment = get_object_or_404(Appointment, pk=pk)
    try:
        finish_appointment(appointment=appointment, actor=request.user)
        messages.success(request, "Servicio completado.")
    except (PermissionDenied, ValidationError) as exc:
        messages.error(request, getattr(exc, "message", str(exc)))
    return redirect("service_requests:detail", pk=appointment.service_request_id)


@login_required
def appointment_confirm(request, pk):
    if request.method != "POST":
        raise PermissionDenied
    appointment = get_object_or_404(Appointment, pk=pk)
    try:
        confirm_appointment(appointment=appointment, actor=request.user)
        messages.success(request, "La cita fue confirmada.")
    except (PermissionDenied, ValidationError) as exc:
        messages.error(request, getattr(exc, "message", str(exc)))
    return redirect("service_requests:appointment_detail", pk=pk)
