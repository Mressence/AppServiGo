from datetime import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from technicians.models import TechnicianProfile, TechnicianAvailability, AvailabilityException
from notifications.services import notify
from .models import (
    ServiceRequest, Quotation, Appointment, Cancellation, ServiceHistory,
)


def _is_admin(user):
    return user.is_staff or getattr(user, "role", "") == User.Role.ADMINISTRADOR


def record_history(service_request, actor, action, previous="", new="", description=""):
    return ServiceHistory.objects.create(
        service_request=service_request, actor=actor, action=action,
        previous_value=str(previous), new_value=str(new), description=description,
    )


def _validate_technician_slot(technician, start_at, end_at, exclude_appointment=None, exclude_request=None):
    if timezone.is_naive(start_at):
        start_at = timezone.make_aware(start_at, timezone.get_current_timezone())
    if timezone.is_naive(end_at):
        end_at = timezone.make_aware(end_at, timezone.get_current_timezone())
    if start_at <= timezone.now():
        raise ValidationError("Selecciona una fecha y hora futuras.")
    if end_at <= start_at:
        raise ValidationError("La hora final debe ser posterior a la inicial.")

    local_start = timezone.localtime(start_at)
    local_end = timezone.localtime(end_at)
    if local_start.date() != local_end.date():
        raise ValidationError("La cita debe comenzar y terminar el mismo día.")

    weekly = TechnicianAvailability.objects.filter(
        technician=technician, weekday=local_start.weekday(), active=True,
        start_time__lte=local_start.time(), end_time__gte=local_end.time(),
    ).exists()
    if not weekly:
        raise ValidationError("El técnico no tiene disponibilidad para ese día y horario.")

    if AvailabilityException.objects.filter(
        technician=technician, start_at__lt=end_at, end_at__gt=start_at,
    ).exists():
        raise ValidationError("El técnico bloqueó ese período.")

    conflicts = Appointment.objects.filter(
        technician=technician,
        status__in=[Appointment.Status.PROGRAMADA, Appointment.Status.CONFIRMADA],
        start_at__lt=end_at, end_at__gt=start_at,
    )
    if exclude_appointment:
        conflicts = conflicts.exclude(pk=exclude_appointment.pk)
    if conflicts.exists():
        raise ValidationError("Ese horario ya está reservado. Selecciona otro.")

    pending_requests = ServiceRequest.objects.filter(
        assigned_technician=technician,
        status__in=[
            ServiceRequest.Status.PENDIENTE,
            ServiceRequest.Status.COTIZADA,
            ServiceRequest.Status.ACEPTADA,
            ServiceRequest.Status.PROGRAMADA,
            ServiceRequest.Status.EN_EJECUCION,
        ],
        requested_start_at__lt=end_at,
        requested_end_at__gt=start_at,
    ).exclude(
        appointment__status__in=[Appointment.Status.CANCELADA, Appointment.Status.COMPLETADA]
    )
    if exclude_request is not None:
        pending_requests = pending_requests.exclude(pk=exclude_request.pk)
    if pending_requests.exists():
        raise ValidationError("Ese horario ya fue solicitado por otro cliente. Selecciona otro.")


@transaction.atomic
def create_quotation(*, request_obj, technician, amount, details, estimated_days):
    profile = getattr(technician, "technician_profile", None)
    if technician.role != User.Role.TECNICO or not profile or profile.status != TechnicianProfile.Status.APROBADO:
        raise PermissionDenied("Solo los técnicos aprobados pueden cotizar.")
    if request_obj.assigned_technician_id != technician.pk:
        raise PermissionDenied("Esta solicitud fue asignada a otro técnico. No puedes verla ni cotizarla.")
    if not profile.category_id or profile.category_id != request_obj.service_type.category_id:
        raise PermissionDenied("Tu categoría profesional ya no coincide con el servicio solicitado.")
    if request_obj.requester_id == technician.pk:
        raise PermissionDenied("No puedes cotizar tu propia solicitud.")
    if request_obj.status not in (ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA):
        raise ValidationError("Esta solicitud ya no acepta cotizaciones.")

    quotation, created = Quotation.objects.update_or_create(
        service_request=request_obj, technician=technician,
        defaults={"amount": amount, "details": details,
                  "estimated_days": estimated_days, "status": Quotation.Status.ENVIADA},
    )
    if request_obj.status == ServiceRequest.Status.PENDIENTE:
        old = request_obj.status
        request_obj.status = ServiceRequest.Status.COTIZADA
        request_obj.save(update_fields=["status", "updated_at"])
        record_history(request_obj, technician, "Cotización enviada", old, request_obj.status)
    notify(
        request_obj.requester, "Te llegó una cotización",
        f"El técnico {technician.get_full_name() or technician.username} envió una cotización de B/. {amount} para tu solicitud #{request_obj.pk}.",
        "QUOTATION", f"/solicitudes/{request_obj.pk}/",
    )
    return quotation, created


@transaction.atomic
def accept_quotation(*, quotation, requester):
    request_obj = ServiceRequest.objects.select_for_update().get(pk=quotation.service_request_id)
    if request_obj.requester_id != requester.pk:
        raise PermissionDenied("Solo quien creó la solicitud puede aceptar una cotización.")
    if request_obj.assigned_technician_id != quotation.technician_id:
        raise PermissionDenied("La cotización no corresponde al técnico asignado a esta solicitud.")
    if request_obj.status != ServiceRequest.Status.COTIZADA or quotation.status != Quotation.Status.ENVIADA:
        raise ValidationError("Esta cotización ya no puede aceptarse.")

    # Si el cliente eligió día y hora desde el calendario, se valida y agenda al aceptar.
    if request_obj.requested_start_at and request_obj.requested_end_at:
        _validate_technician_slot(
            quotation.technician, request_obj.requested_start_at,
            request_obj.requested_end_at,
            exclude_request=request_obj,
        )

    quotation.status = Quotation.Status.ACEPTADA
    quotation.save(update_fields=["status", "updated_at"])
    request_obj.quotations.exclude(pk=quotation.pk).update(status=Quotation.Status.RECHAZADA)
    previous = request_obj.status
    request_obj.assigned_technician = quotation.technician
    request_obj.status = ServiceRequest.Status.ACEPTADA
    request_obj.save(update_fields=["assigned_technician", "status", "updated_at"])
    record_history(request_obj, requester, "Cotización aceptada", previous, request_obj.status)
    notify(requester, "Cotización aceptada", f"Aceptaste la cotización del técnico para la solicitud #{request_obj.pk}.",
           "QUOTATION", f"/solicitudes/{request_obj.pk}/")
    notify(quotation.technician, "Cotización aceptada", f"El cliente aceptó tu cotización para la solicitud #{request_obj.pk}.",
           "QUOTATION", f"/solicitudes/{request_obj.pk}/")

    if request_obj.requested_start_at and request_obj.requested_end_at:
        appointment = Appointment.objects.create(
            service_request=request_obj, technician=quotation.technician,
            start_at=request_obj.requested_start_at,
            end_at=request_obj.requested_end_at,
            notes="Horario elegido por el cliente desde el calendario.",
            created_by=requester,
        )
        old = request_obj.status
        request_obj.status = ServiceRequest.Status.PROGRAMADA
        request_obj.save(update_fields=["status", "updated_at"])
        record_history(request_obj, requester, "Cita programada al aceptar cotización", old, request_obj.status)
        notify(requester, "Cita programada", "Tu cotización fue aceptada y la cita quedó programada.",
               "APPOINTMENT", f"/solicitudes/cita/{appointment.pk}/")
        notify(quotation.technician, "Cotización aceptada y cita programada",
               f"El cliente aceptó tu cotización. Cita: {timezone.localtime(appointment.start_at):%d/%m/%Y %H:%M}.",
               "APPOINTMENT", f"/solicitudes/cita/{appointment.pk}/")
    else:
        notify(requester, "Selecciona la fecha de tu servicio", "Tu cotización fue aceptada. Ya puedes programar la cita.",
               "APPOINTMENT", f"/solicitudes/{request_obj.pk}/")
    return request_obj


@transaction.atomic
def transition_request(*, request_obj, actor, target_status, cancellation_reason=''):
    is_admin = _is_admin(actor)
    is_owner = request_obj.requester_id == actor.pk
    is_assigned = request_obj.assigned_technician_id == actor.pk
    transitions = {
        ServiceRequest.Status.ACEPTADA: {ServiceRequest.Status.EN_EJECUCION, ServiceRequest.Status.COMPLETADA},
        ServiceRequest.Status.PROGRAMADA: {ServiceRequest.Status.EN_EJECUCION, ServiceRequest.Status.COMPLETADA},
        ServiceRequest.Status.EN_EJECUCION: {ServiceRequest.Status.COMPLETADA},
    }
    if target_status == ServiceRequest.Status.CANCELADA:
        if not cancellation_reason.strip():
            raise ValidationError("Indica el motivo de la cancelación.")
        if not (is_owner or is_admin or is_assigned):
            raise PermissionDenied("No puedes cancelar esta solicitud.")
        if request_obj.status in (ServiceRequest.Status.COMPLETADA, ServiceRequest.Status.CANCELADA):
            raise ValidationError("El servicio ya está cerrado.")
    else:
        if target_status not in transitions.get(request_obj.status, set()):
            raise ValidationError("La transición solicitada no está permitida desde el estado actual.")
        if target_status == ServiceRequest.Status.EN_EJECUCION and not Appointment.objects.filter(service_request=request_obj, status__in=[Appointment.Status.PROGRAMADA, Appointment.Status.CONFIRMADA]).exists():
            raise ValidationError("Primero debe existir una cita programada o confirmada.")
        if not (is_admin or is_assigned):
            raise PermissionDenied("Solo el técnico asignado o el administrador puede actualizar el trabajo.")
        if not is_admin:
            profile = getattr(actor, "technician_profile", None)
            if not profile or profile.status != TechnicianProfile.Status.APROBADO:
                raise PermissionDenied("El técnico debe estar aprobado.")

    previous = request_obj.status
    request_obj.status = target_status
    request_obj.save(update_fields=["status", "updated_at"])
    record_history(
        request_obj, actor, "Estado del servicio actualizado", previous, target_status,
        cancellation_reason.strip() if target_status == ServiceRequest.Status.CANCELADA else "",
    )

    appointment = getattr(request_obj, "appointment", None)
    if appointment and target_status in (ServiceRequest.Status.COMPLETADA, ServiceRequest.Status.CANCELADA):
        appointment.status = Appointment.Status.COMPLETADA if target_status == ServiceRequest.Status.COMPLETADA else Appointment.Status.CANCELADA
        appointment.save(update_fields=["status", "updated_at"])

    if target_status == ServiceRequest.Status.CANCELADA:
        Cancellation.objects.create(
            service_request=request_obj, appointment=appointment,
            cancelled_by=actor, reason=cancellation_reason.strip(), previous_status=previous,
        )

    status_text = request_obj.get_status_display()
    notification_title = "Servicio cancelado" if target_status == ServiceRequest.Status.CANCELADA else f"Estado actualizado: {status_text}"
    notification_message = (
        f"El servicio #{request_obj.pk} fue cancelado. Motivo: {cancellation_reason.strip()}"
        if target_status == ServiceRequest.Status.CANCELADA
        else f"Tu servicio #{request_obj.pk} ahora está: {status_text}."
    )
    if request_obj.requester_id != actor.pk:
        notify(request_obj.requester, notification_title, notification_message,
               "CANCELLATION" if target_status == ServiceRequest.Status.CANCELADA else "REQUEST",
               f"/solicitudes/{request_obj.pk}/")
    if request_obj.assigned_technician_id and request_obj.assigned_technician_id != actor.pk:
        notify(request_obj.assigned_technician, notification_title, notification_message,
               "CANCELLATION" if target_status == ServiceRequest.Status.CANCELADA else "REQUEST",
               f"/solicitudes/{request_obj.pk}/")
    return request_obj


@transaction.atomic
def create_appointment(*, request_obj, actor, start_at, end_at, notes=""):
    is_admin = _is_admin(actor)
    if request_obj.requester_id != actor.pk and not is_admin:
        raise PermissionDenied("Solo el cliente propietario o el administrador puede programar la cita.")
    if request_obj.status not in (ServiceRequest.Status.ACEPTADA, ServiceRequest.Status.PROGRAMADA):
        raise ValidationError("Primero debe aceptarse la cotización.")
    if not request_obj.assigned_technician_id:
        raise ValidationError("La solicitud no tiene un técnico asignado.")
    if Appointment.objects.filter(service_request=request_obj).exists():
        raise ValidationError("Esta solicitud ya tiene una cita. Utiliza la opción de reprogramar.")
    User.objects.select_for_update().get(pk=request_obj.assigned_technician_id)
    _validate_technician_slot(request_obj.assigned_technician, start_at, end_at, exclude_request=request_obj)
    appointment = Appointment.objects.create(
        service_request=request_obj, technician=request_obj.assigned_technician,
        start_at=start_at, end_at=end_at, notes=notes, created_by=actor,
    )
    previous = request_obj.status
    request_obj.status = ServiceRequest.Status.PROGRAMADA
    request_obj.requested_start_at = start_at
    request_obj.requested_end_at = end_at
    request_obj.preferred_date = timezone.localtime(start_at).date()
    request_obj.save(update_fields=[
        "status", "requested_start_at", "requested_end_at", "preferred_date", "updated_at",
    ])
    record_history(request_obj, actor, "Cita programada", previous, request_obj.status)
    notify(request_obj.requester, "Cita programada", "Tu cita quedó programada.",
           "APPOINTMENT", f"/solicitudes/cita/{appointment.pk}/")
    notify(appointment.technician, "Nueva cita asignada",
           f"Se programó una cita para la solicitud #{request_obj.pk}.",
           "APPOINTMENT", f"/solicitudes/cita/{appointment.pk}/")
    return appointment


@transaction.atomic
def reschedule_appointment(*, appointment, actor, start_at, end_at, notes=""):
    request_obj = appointment.service_request
    if not (_is_admin(actor) or request_obj.requester_id == actor.pk or appointment.technician_id == actor.pk):
        raise PermissionDenied("No tienes permiso para reprogramar esta cita.")
    if appointment.status in (Appointment.Status.CANCELADA, Appointment.Status.COMPLETADA):
        raise ValidationError("No se puede reprogramar una cita cerrada.")
    _validate_technician_slot(
        appointment.technician, start_at, end_at,
        exclude_appointment=appointment, exclude_request=request_obj,
    )
    previous = f"{appointment.start_at} - {appointment.end_at}"
    appointment.start_at, appointment.end_at = start_at, end_at
    appointment.notes = notes
    appointment.status = Appointment.Status.PROGRAMADA
    appointment.save()
    request_obj.requested_start_at = start_at
    request_obj.requested_end_at = end_at
    request_obj.preferred_date = timezone.localtime(start_at).date()
    request_obj.save(update_fields=["requested_start_at", "requested_end_at", "preferred_date", "updated_at"])
    record_history(request_obj, actor, "Cita reprogramada", previous, f"{start_at} - {end_at}")
    for recipient, title, msg in [
        (request_obj.requester, "Cita reprogramada", "La fecha y hora de tu servicio fueron modificadas."),
        (appointment.technician, "Cita reprogramada", "La fecha y hora de un servicio asignado fueron modificadas."),
    ]:
        if recipient.pk != actor.pk:
            notify(recipient, title, msg, "APPOINTMENT", f"/solicitudes/cita/{appointment.pk}/")
    return appointment


@transaction.atomic
def cancel_appointment(*, appointment, actor, reason):
    request_obj = appointment.service_request
    if not (_is_admin(actor) or request_obj.requester_id == actor.pk or appointment.technician_id == actor.pk):
        raise PermissionDenied("No tienes permiso para cancelar esta cita.")
    if appointment.status in (Appointment.Status.CANCELADA, Appointment.Status.COMPLETADA):
        raise ValidationError("La cita ya está cerrada.")
    previous = appointment.status
    appointment.status = Appointment.Status.CANCELADA
    appointment.save(update_fields=["status", "updated_at"])
    Cancellation.objects.create(service_request=request_obj, appointment=appointment,
                                cancelled_by=actor, reason=reason, previous_status=previous)
    old_request_status = request_obj.status
    request_obj.status = ServiceRequest.Status.CANCELADA
    request_obj.save(update_fields=["status", "updated_at"])
    record_history(request_obj, actor, "Cita cancelada", previous, appointment.status, reason)
    for recipient in (request_obj.requester, appointment.technician):
        if recipient.pk != actor.pk:
            notify(recipient, "Cita cancelada", reason, "CANCELLATION", f"/solicitudes/{request_obj.pk}/")
    return appointment


@transaction.atomic
def finish_appointment(*, appointment, actor):
    request_obj = appointment.service_request
    if not (_is_admin(actor) or appointment.technician_id == actor.pk):
        raise PermissionDenied("Solo el técnico asignado o administrador puede completar el servicio.")
    if appointment.status not in (Appointment.Status.PROGRAMADA, Appointment.Status.CONFIRMADA):
        raise ValidationError("La cita no se puede completar en su estado actual.")
    appointment.status = Appointment.Status.COMPLETADA
    appointment.save(update_fields=["status", "updated_at"])
    previous = request_obj.status
    request_obj.status = ServiceRequest.Status.COMPLETADA
    request_obj.save(update_fields=["status", "updated_at"])
    record_history(request_obj, actor, "Servicio completado", previous, request_obj.status)
    notify(request_obj.requester, "Servicio completado", f"El técnico marcó como completado tu servicio #{request_obj.pk}.",
           "REQUEST", f"/solicitudes/{request_obj.pk}/")
    if request_obj.assigned_technician_id != actor.pk:
        notify(request_obj.assigned_technician, "Servicio completado", f"El servicio #{request_obj.pk} fue marcado como completado.",
               "REQUEST", f"/solicitudes/{request_obj.pk}/")
    return appointment


@transaction.atomic
def confirm_appointment(*, appointment, actor):
    request_obj = appointment.service_request
    if not (_is_admin(actor) or request_obj.requester_id == actor.pk or appointment.technician_id == actor.pk):
        raise PermissionDenied("No tienes permiso para confirmar esta cita.")
    if appointment.status != Appointment.Status.PROGRAMADA:
        raise ValidationError("Solo se pueden confirmar citas programadas.")
    appointment.status = Appointment.Status.CONFIRMADA
    appointment.save(update_fields=["status", "updated_at"])
    record_history(request_obj, actor, "Cita confirmada", Appointment.Status.PROGRAMADA, Appointment.Status.CONFIRMADA)
    other = appointment.technician if actor.pk == request_obj.requester_id else request_obj.requester
    notify(other, "Cita confirmada", "La cita del servicio fue confirmada.",
           "APPOINTMENT", f"/solicitudes/cita/{appointment.pk}/")
    return appointment
