
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
