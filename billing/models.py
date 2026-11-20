import uuid

from django.conf import settings
from django.db import models
from service_requests.models import ServiceRequest


class Invoice(models.Model):
    """Datos mínimos de factura; el archivo PDF se genera al descargar y no se almacena."""
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.PROTECT, related_name="invoice")
    invoice_number = models.CharField(max_length=30, unique=True, blank=True)
    issued_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invoices")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at"]
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"

    def save(self, *args, **kwargs):
        if not self.invoice_number and self.pk is None:
            self.invoice_number = f"SG-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number or f"Factura solicitud {self.service_request_id}"
