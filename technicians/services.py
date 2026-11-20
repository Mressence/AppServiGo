from datetime import datetime, timedelta

from django.utils import timezone

from .models import TechnicianAvailability, AvailabilityException
from service_requests.models import Appointment, ServiceRequest


def available_start_times(technician, day, duration_minutes=60, step_minutes=30, exclude_request=None):
    """Devuelve horas de inicio disponibles en la zona horaria del proyecto."""
    now = timezone.localtime()
    results = []
    slots = TechnicianAvailability.objects.filter(
        technician=technician, weekday=day.weekday(), active=True,
    ).order_by("start_time")
    for weekly in slots:
        cursor = datetime.combine(day, weekly.start_time)
        limit = datetime.combine(day, weekly.end_time)
        while cursor + timedelta(minutes=duration_minutes) <= limit:
            start_naive = cursor
            end_naive = cursor + timedelta(minutes=duration_minutes)
            start_at = timezone.make_aware(start_naive, timezone.get_current_timezone())
            end_at = timezone.make_aware(end_naive, timezone.get_current_timezone())
            if start_at > timezone.now():
                blocked = AvailabilityException.objects.filter(
                    technician=technician, start_at__lt=end_at, end_at__gt=start_at,
                ).exists()
                busy_appointment = Appointment.objects.filter(
                    technician=technician,
                    status__in=[Appointment.Status.PROGRAMADA, Appointment.Status.CONFIRMADA],
                    start_at__lt=end_at, end_at__gt=start_at,
                ).exists()
                # A slot selected by a client is reserved provisionally while the
                # technician prepares the quote. It must not be offered to others.
                busy_requests = ServiceRequest.objects.filter(
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
                )
                if exclude_request is not None:
                    busy_requests = busy_requests.exclude(pk=exclude_request.pk)
                busy_request = busy_requests.exclude(
                    appointment__status__in=[
                        Appointment.Status.CANCELADA,
                        Appointment.Status.COMPLETADA,
                    ]
                ).exists()
                if not blocked and not busy_appointment and not busy_request:
                    results.append((cursor.strftime("%H:%M"), f"{cursor:%H:%M} – {end_naive:%H:%M}"))
            cursor += timedelta(minutes=step_minutes)
    return results
