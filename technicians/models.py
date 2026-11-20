
from django.conf import settings
from django.db import models


class TechnicianProfile(models.Model):

    class Status(models.TextChoices):
        BORRADOR = "BORRADOR", "Sin enviar"
        PENDIENTE = "PENDIENTE", "Pendiente de revisión"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Requiere correcciones"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="technician_profile",
    )

    professional_title = models.CharField(
        "Especialidad / título profesional",
        max_length=150,
    )

    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="technicians",
        verbose_name="Categoría profesional",
        help_text=(
            "El administrador debe asignar una categoría activa "
            "antes de aprobar al técnico."
        ),
    )

    description = models.TextField(
        "Descripción profesional",
        blank=True,
    )

    experience = models.PositiveIntegerField(
        "Años de experiencia",
        default=0,
    )

    phone = models.CharField(
        "Teléfono profesional",
        max_length=30,
        blank=True,
    )

    identity_document = models.FileField(
        "Documento de identidad (PDF o imagen)",
        upload_to="technician_documents/",
        blank=True,
        null=True,
    )

    professional_document = models.FileField(
        "Título o certificación (PDF o imagen)",
        upload_to="technician_documents/",
        blank=True,
        null=True,
    )

    additional_document = models.FileField(
        "Documento adicional (opcional)",
        upload_to="technician_documents/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BORRADOR,
    )

    rejection_reason = models.TextField(
        "Motivo de rechazo",
        blank=True,
    )

    admin_feedback = models.TextField(
        "Retroalimentación del administrador",
        blank=True,
    )

    submitted_at = models.DateTimeField(
        "Fecha de envío",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} — {self.get_status_display()}"


class TechnicianAvailability(models.Model):
    """Franja semanal recurrente; weekday usa lunes=0 ... domingo=6."""
    WEEKDAYS = [(0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"), (4, "Viernes"), (5, "Sábado"), (6, "Domingo")]
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availability_slots")
    weekday = models.PositiveSmallIntegerField("Día", choices=WEEKDAYS)
    start_time = models.TimeField("Desde")
    end_time = models.TimeField("Hasta")
    active = models.BooleanField("Activo", default=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        constraints = [
            models.CheckConstraint(condition=models.Q(start_time__lt=models.F("end_time")), name="tech_availability_valid_range"),
            models.UniqueConstraint(fields=["technician", "weekday", "start_time", "end_time"], name="unique_tech_weekly_slot"),
        ]
        verbose_name = "Horario disponible"
        verbose_name_plural = "Horarios disponibles"

    def __str__(self):
        return f"{self.technician} · {self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class AvailabilityException(models.Model):
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availability_exceptions")
    start_at = models.DateTimeField("Desde")
    end_at = models.DateTimeField("Hasta")
    reason = models.CharField("Motivo", max_length=180, blank=True)

    class Meta:
        ordering = ["start_at"]
        constraints = [models.CheckConstraint(condition=models.Q(start_at__lt=models.F("end_at")), name="tech_exception_valid_range")]
        verbose_name = "Bloqueo de disponibilidad"
        verbose_name_plural = "Bloqueos de disponibilidad"

    def __str__(self):
        return f"{self.technician} · {self.start_at:%d/%m/%Y %H:%M}"
