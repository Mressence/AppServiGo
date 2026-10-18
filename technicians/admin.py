from django.contrib import admin, messages
from django.utils import timezone
from .models import TechnicianProfile
from accounts.models import User


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "professional_title", "experience", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email", "professional_title")
    readonly_fields = ("created_at", "updated_at", "submitted_at")
    actions = ("approve_selected", "reject_selected")
    fieldsets = (
        ("Solicitante", {"fields": ("user", "professional_title", "description", "experience", "phone")}),
        ("Documentos", {"fields": ("identity_document", "professional_document", "additional_document")}),
        ("Revisión", {"fields": ("status", "admin_feedback", "rejection_reason", "submitted_at")}),
        ("Fechas", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status == TechnicianProfile.Status.APROBADO:
            User.objects.filter(pk=obj.user_id).update(role=User.Role.TECNICO)
        elif obj.status in (TechnicianProfile.Status.RECHAZADO, TechnicianProfile.Status.BORRADOR, TechnicianProfile.Status.PENDIENTE):
            User.objects.filter(pk=obj.user_id).update(role=User.Role.USUARIO)

    @admin.action(description="Aprobar técnicos seleccionados")
    def approve_selected(self, request, queryset):
        count = 0
        for profile in queryset.select_related("user"):
            profile.status = TechnicianProfile.Status.APROBADO
            profile.admin_feedback = profile.admin_feedback or "Tu solicitud fue aprobada. Ya puedes acceder a las funciones para técnicos."
            profile.rejection_reason = ""
            profile.save(update_fields=["status", "admin_feedback", "rejection_reason", "updated_at"])
            User.objects.filter(pk=profile.user_id).update(role=User.Role.TECNICO)
            count += 1
        self.message_user(request, f"Se aprobaron {count} solicitud(es).", messages.SUCCESS)

    @admin.action(description="Marcar solicitudes como rechazadas")
    def reject_selected(self, request, queryset):
        count = 0
        for profile in queryset.select_related("user"):
            profile.status = TechnicianProfile.Status.RECHAZADO
            if not profile.admin_feedback:
                profile.admin_feedback = "Tu solicitud requiere correcciones. Revisa los documentos y vuelve a enviarla."
            profile.rejection_reason = profile.admin_feedback
            profile.save(update_fields=["status", "admin_feedback", "rejection_reason", "updated_at"])
            User.objects.filter(pk=profile.user_id).update(role=User.Role.USUARIO)
            count += 1
        self.message_user(request, f"{count} solicitud(es) marcada(s) para corrección. Edita la retroalimentación en cada registro si hace falta.", messages.WARNING)
