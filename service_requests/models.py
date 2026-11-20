from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from catalog.models import ServiceType
from django.core.validators import MinValueValidator, MaxValueValidator


ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024


def validate_attachment(uploaded):
    extension = Path(uploaded.name).suffix.lower()
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise ValidationError("Adjunta únicamente archivos PDF, JPG, JPEG, PNG o WEBP.")
    if uploaded.size > MAX_ATTACHMENT_SIZE:
        raise ValidationError("Cada archivo debe pesar como máximo 10 MB.")


class ServiceRequest(models.Model):
    class Status(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Esperando cotizaciones"
        COTIZADA = "COTIZADA", "Con cotizaciones"
        ACEPTADA = "ACEPTADA", "Cotización aceptada"
        PROGRAMADA = "PROGRAMADA", "Programada"
        EN_EJECUCION = "EN_EJECUCION", "En ejecución"
        COMPLETADA = "COMPLETADA", "Completada"
        CANCELADA = "CANCELADA", "Cancelada"

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="service_requests", verbose_name="Solicitante")
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT, related_name="service_requests", verbose_name="Servicio")
    description = models.TextField("Descripción de la necesidad")
    address = models.TextField("Dirección donde se prestará el servicio")
    preferred_date = models.DateField("Fecha preferida", null=True, blank=True)
    requested_start_at = models.DateTimeField("Horario solicitado", null=True, blank=True)
    requested_end_at = models.DateTimeField("Fin del horario solicitado", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDIENTE)
    assigned_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="assigned_service_requests", verbose_name="Técnico asignado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Solicitud de servicio"
        verbose_name_plural = "Solicitudes de servicio"

    def __str__(self):
        return f"Solicitud #{self.pk} — {self.service_type.name}"


class RequestAttachment(models.Model):
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField("Archivo", upload_to="request_evidence/%Y/%m/", validators=[validate_attachment])
    description = models.CharField("Descripción", max_length=180, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="request_attachments")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]
        verbose_name = "Adjunto / evidencia"
        verbose_name_plural = "Adjuntos / evidencias"

    def __str__(self):
        return self.file.name.rsplit("/", 1)[-1]


class Quotation(models.Model):
    class Status(models.TextChoices):
        ENVIADA = "ENVIADA", "Enviada"
        ACEPTADA = "ACEPTADA", "Aceptada"
        RECHAZADA = "RECHAZADA", "No seleccionada"

    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="quotations", verbose_name="Solicitud")
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="quotations", verbose_name="Técnico")
    amount = models.DecimalField("Precio propuesto", max_digits=10, decimal_places=2)
    details = models.TextField("Detalle de la cotización")
    estimated_days = models.PositiveIntegerField("Duración estimada (días)", default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENVIADA)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["amount", "created_at"]
        constraints = [models.UniqueConstraint(fields=["service_request", "technician"], name="unique_quote_per_technician_request")]
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"

    def __str__(self):
        return f"Cotización #{self.pk} — {self.amount}"
from django.core.validators import MinValueValidator, MaxValueValidator


class TechnicianReview(models.Model):
    service_request = models.OneToOneField(
        "service_requests.ServiceRequest",
        on_delete=models.CASCADE,
        related_name="technician_review",
    )
    technician = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="received_technician_reviews",
    )
    reviewer = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="written_technician_reviews",
    )
    rating = models.PositiveSmallIntegerField(
        "Calificación",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField("Comentario", blank=True)
    created_at = models.DateTimeField("Fecha de publicación", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="technician_review_rating_1_5",
            ),
        ]

    def __str__(self):
        return f"{self.technician} — {self.rating}/5"

class Appointment(models.Model):
    class Status(models.TextChoices):
        PROGRAMADA = "PROGRAMADA", "Programada"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        COMPLETADA = "COMPLETADA", "Completada"
        CANCELADA = "CANCELADA", "Cancelada"

    service_request = models.OneToOneField(ServiceRequest, on_delete=models.PROTECT, related_name="appointment", verbose_name="Solicitud")
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="technician_appointments")
    start_at = models.DateTimeField("Inicio")
    end_at = models.DateTimeField("Finalización")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PROGRAMADA)
    notes = models.TextField("Notas", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_appointments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at"]
        constraints = [models.CheckConstraint(condition=models.Q(start_at__lt=models.F("end_at")), name="appointment_valid_range")]
        verbose_name = "Cita"
        verbose_name_plural = "Citas"

    def __str__(self):
        return f"Cita #{self.service_request_id} · {self.start_at:%d/%m/%Y %H:%M}"


class Cancellation(models.Model):
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.PROTECT, related_name="cancellations")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="cancellations")
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="service_cancellations")
    reason = models.TextField("Motivo")
    previous_status = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Cancelación"
        verbose_name_plural = "Cancelaciones"


class ServiceHistory(models.Model):
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="history")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="service_history_actions")
    action = models.CharField(max_length=100)
    previous_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Movimiento de historial"
        verbose_name_plural = "Historial de servicios"
