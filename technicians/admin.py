from django import forms
from django.contrib import admin, messages
from catalog.models import Category
from accounts.models import User
from .models import TechnicianProfile


class TechnicianProfileAdminForm(forms.ModelForm):
    class Meta:
        model = TechnicianProfile
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        category = cleaned.get("category")
        if status == TechnicianProfile.Status.APROBADO:
            if not category:
                self.add_error("category", "Asigna una categoría profesional antes de aprobar al técnico.")
            elif not category.active:
                self.add_error("category", "La categoría seleccionada está inactiva. Elige una categoría activa.")
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
        ("Solicitante", {"fields": ("user", "professional_title", "category", "description", "experience", "phone",)}),
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
    count = 0
    errors = []

    for profile in queryset.select_related("user", "category"):
        if not profile.category_id:
            errors.append(
                f"{profile.user}: falta la categoría profesional."
            )
            continue

        if not profile.category.active:
            errors.append(
                f"{profile.user}: la categoría está desactivada."
            )
            continue

        if not profile.identity_document or not profile.professional_document:
            errors.append(
                f"{profile.user}: faltan documentos obligatorios."
            )
            continue

        profile.status = TechnicianProfile.Status.APROBADO
        profile.admin_feedback = (
            "Tu solicitud fue aprobada. Ya puedes acceder a las funciones de técnico."
        )
        profile.rejection_reason = ""
        profile.full_clean()
        profile.save()

        User.objects.filter(pk=profile.user_id).update(
            role=User.Role.TECNICO
        )
        count += 1

    if count:
        self.message_user(
            request,
            f"Se aprobaron {count} solicitud(es).",
            messages.SUCCESS,
        )

    if errors:
        self.message_user(
            request,
            "No se aprobaron estas solicitudes: " + " ".join(errors),
            messages.ERROR,
        )


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
