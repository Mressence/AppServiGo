from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from accounts.models import User
from technicians.models import TechnicianProfile
from .models import ServiceRequest, Quotation


@transaction.atomic
def create_quotation(*, request_obj, technician, amount, details, estimated_days):
    profile = getattr(technician, "technician_profile", None)
    if technician.role != User.Role.TECNICO or not profile or profile.status != TechnicianProfile.Status.APROBADO:
        raise PermissionDenied("Solo los técnicos aprobados pueden cotizar.")
    if request_obj.requester_id == technician.pk:
        raise PermissionDenied("No puedes cotizar tu propia solicitud.")
    if request_obj.status not in (ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA):
        raise ValidationError("Esta solicitud ya no acepta cotizaciones.")
    quotation, created = Quotation.objects.update_or_create(
        service_request=request_obj,
        technician=technician,
        defaults={"amount": amount, "details": details, "estimated_days": estimated_days, "status": Quotation.Status.ENVIADA},
    )
    if request_obj.status == ServiceRequest.Status.PENDIENTE:
        request_obj.status = ServiceRequest.Status.COTIZADA
        request_obj.save(update_fields=["status", "updated_at"])
    return quotation, created


@transaction.atomic
def accept_quotation(*, quotation, requester):
    request_obj = quotation.service_request
    if request_obj.requester_id != requester.pk:
        raise PermissionDenied("Solo quien creó la solicitud puede aceptar una cotización.")
    if request_obj.status != ServiceRequest.Status.COTIZADA or quotation.status != Quotation.Status.ENVIADA:
        raise ValidationError("Esta cotización ya no puede aceptarse.")
    quotation.status = Quotation.Status.ACEPTADA
    quotation.save(update_fields=["status", "updated_at"])
    request_obj.quotations.exclude(pk=quotation.pk).update(status=Quotation.Status.RECHAZADA)
    request_obj.assigned_technician = quotation.technician
    request_obj.status = ServiceRequest.Status.ACEPTADA
    request_obj.save(update_fields=["assigned_technician", "status", "updated_at"])
    return request_obj


@transaction.atomic
def transition_request(*, request_obj, actor, target_status):
    """Aplica transiciones permitidas y valida quién puede ejecutarlas."""
    is_admin = actor.is_staff or actor.role == User.Role.ADMINISTRADOR
    is_owner = request_obj.requester_id == actor.pk
    is_assigned = request_obj.assigned_technician_id == actor.pk
    transitions = {
        ServiceRequest.Status.ACEPTADA: {ServiceRequest.Status.PROGRAMADA},
        ServiceRequest.Status.PROGRAMADA: {ServiceRequest.Status.EN_EJECUCION},
        ServiceRequest.Status.EN_EJECUCION: {ServiceRequest.Status.COMPLETADA},
    }
    if target_status == ServiceRequest.Status.CANCELADA:
        if not (is_owner or is_admin) or request_obj.status not in (ServiceRequest.Status.PENDIENTE, ServiceRequest.Status.COTIZADA):
            raise PermissionDenied("Solo puedes cancelar tu solicitud antes de aceptar una cotización.")
    else:
        allowed = transitions.get(request_obj.status, set())
        if target_status not in allowed:
            raise ValidationError("La transición solicitada no está permitida desde el estado actual.")
        if not (is_admin or is_assigned):
            raise PermissionDenied("Solo el técnico asignado o el administrador puede actualizar esta etapa.")
        if not is_admin:
            profile = getattr(actor, "technician_profile", None)
            if not profile or profile.status != TechnicianProfile.Status.APROBADO:
                raise PermissionDenied("El técnico debe estar aprobado para gestionar el servicio.")
    request_obj.status = target_status
    request_obj.save(update_fields=["status", "updated_at"])
    return request_obj
