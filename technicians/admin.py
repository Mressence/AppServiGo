from django import forms
from django.contrib import admin, messages
from accounts.models import User
from .models import TechnicianProfile, TechnicianAvailability, AvailabilityException


class TechnicianProfileAdminForm(forms.ModelForm):
    class Meta:
        model = TechnicianProfile
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("status") == TechnicianProfile.Status.APROBADO:
            category = cleaned.get("category")
            if not category:
                self.add_error("category", "Asigna una categoría profesional antes de aprobar al técnico.")
            elif not category.active:
                self.add_error("category", "La categoría seleccionada está inactiva.")
        return cleaned


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    form = TechnicianProfileAdminForm
    list_display = ("user", "professional_title", "category", "experience", "status", "submitted_at")
    list_filter = ("status", "category", "category__active")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email", "professional_title", "category__name")
    autocomplete_fields = ("category",)
    readonly_fields = ("created_at", "updated_at", "submitted_at")
    actions = ("approve_selected", "reject_selected")
    fieldsets = (
        ("Solicitante", {"fields": ("user", "professional_title", "category", "description", "experience", "phone")}),
        ("Documentos", {"fields": ("identity_document", "professional_document", "additional_document")}),
        ("Revisión", {"fields": ("status", "admin_feedback", "rejection_reason", "submitted_at")}),
        ("Fechas", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        if obj.status == TechnicianProfile.Status.APROBADO and (not obj.category_id or not obj.category.active):
            obj.status = TechnicianProfile.Status.PENDIENTE
            self.message_user(request, "No se aprobó: asigna una categoría profesional activa.", messages.ERROR)
        super().save_model(request, obj, form, change)
        if obj.status == TechnicianProfile.Status.APROBADO:
            User.objects.filter(pk=obj.user_id).update(role=User.Role.TECNICO)
        else:
            User.objects.filter(pk=obj.user_id).update(role=User.Role.USUARIO)

    @admin.action(description="Aprobar técnicos seleccionados")
    def approve_selected(self, request, queryset):
        count, errors = 0, []
        for profile in queryset.select_related("user", "category"):
            if not profile.category_id or not profile.category.active:
                errors.append(f"{profile.user}: falta una categoría activa.")
                continue
            if not profile.identity_document or not profile.professional_document:
                errors.append(f"{profile.user}: faltan documentos obligatorios.")
                continue
            profile.status = TechnicianProfile.Status.APROBADO
            profile.admin_feedback = "Tu solicitud fue aprobada. Ya puedes gestionar servicios."
            profile.rejection_reason = ""
            profile.save()
            User.objects.filter(pk=profile.user_id).update(role=User.Role.TECNICO)
            count += 1
        if count:
            self.message_user(request, f"Se aprobaron {count} técnico(s).", messages.SUCCESS)
        if errors:
            self.message_user(request, "No se aprobaron: " + " ".join(errors), messages.ERROR)

    @admin.action(description="Marcar solicitudes para corrección")
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
        self.message_user(request, f"{count} solicitud(es) marcada(s) para corrección.", messages.WARNING)


@admin.register(TechnicianAvailability)
class TechnicianAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("technician", "weekday", "start_time", "end_time", "active")
    list_filter = ("weekday", "active")
    search_fields = ("technician__username", "technician__email")


@admin.register(AvailabilityException)
class AvailabilityExceptionAdmin(admin.ModelAdmin):
    list_display = ("technician", "start_at", "end_at", "reason")
    list_filter = ("start_at",)
    search_fields = ("technician__username", "reason")
