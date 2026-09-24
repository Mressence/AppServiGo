from django.conf import settings
from django.db import models


class TechnicianProfile(models.Model):

    class Status(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"

    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="technician_profile")
    professional_title = models.CharField(max_length=150,blank=True)
    description = models.TextField(blank=True)
    experience = models.PositiveIntegerField(default=0)
    phone = models.CharField(max_length=30,blank=True)
    identity_document = models.FileField(upload_to="technician_documents/",blank=True,null=True)
    professional_document = models.FileField(upload_to="technician_documents/",blank=True,null=True)
    additional_document = models.FileField(upload_to="technician_documents/",blank=True,null=True)
    status = models.CharField(max_length=20,choices=Status.choices,default=Status.PENDIENTE)
    rejection_reason = models.TextField(blank=True)
    admin_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user.username
