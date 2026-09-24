from django.contrib import admin
from .models import TechnicianProfile

@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):

    list_display = ("user","professional_title","experience","status","created_at",)
    list_filter = ("status",)
    search_fields = ("user__username","user__email","professional_title",)
    readonly_fields = ("created_at","updated_at",)
    fieldsets = (
        ("Información del técnico",{"fields": ("user","professional_title","description","experience","phone",)}),

        ("Documentación",{"fields": ("identity_document","professional_document","additional_document",)}),

        ("Revisión",{"fields": ("status","admin_feedback","rejection_reason",)}),

        ("Fechas",{"fields": ("created_at","updated_at",)}),
    )
def approve_technician(modeladmin, request, queryset):

    for technician in queryset:

        technician.status = TechnicianProfile.Status.APROBADO
        technician.admin_feedback = "Solicitud aprobada."
        technician.save()

        technician.user.role = "TECNICO"
        technician.user.save()
def reject_technician(modeladmin, request, queryset):

    for technician in queryset:

        technician.status = TechnicianProfile.Status.RECHAZADO
        technician.user.role = "USUARIO"
        technician.save()

        technician.user.save()