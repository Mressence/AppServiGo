from django.contrib import admin
from .models import TechnicianProfile

@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "professional_title", "experience", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "professional_title")
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Aprobar técnicos seleccionados")
    def approve_selected(self, request, queryset):
        queryset.update(status="APROBADO", rejection_reason="")

    @admin.action(description="Rechazar técnicos seleccionados")
    def reject_selected(self, request, queryset):
        queryset.update(status="RECHAZADO")
