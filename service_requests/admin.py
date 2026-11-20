from django.contrib import admin
from .models import ServiceRequest, RequestAttachment, Quotation, Appointment, Cancellation, ServiceHistory
from accounts.models import User
from technicians.models import TechnicianProfile

class RequestAttachmentInline(admin.TabularInline):
    model = RequestAttachment
    extra = 0
    readonly_fields = ("file", "description", "uploaded_by", "uploaded_at")

class QuotationInline(admin.TabularInline):
    model = Quotation
    extra = 0
    readonly_fields = ("technician", "amount", "details", "estimated_days", "status", "created_at")

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "service_type", "requester", "assigned_technician", "status", "created_at")
    list_filter = ("status", "service_type__category", "created_at")
    search_fields = ("requester__username", "requester__email", "service_type__name", "description")
    readonly_fields = ("created_at", "updated_at")
    inlines = (RequestAttachmentInline, QuotationInline)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_technician":
            kwargs["queryset"] = User.objects.filter(
                role=User.Role.TECNICO,
                technician_profile__status=TechnicianProfile.Status.APROBADO,
                is_active=True,
            ).order_by("first_name", "username")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("id", "service_request", "technician", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("service_request__id", "technician__username", "details")

@admin.register(RequestAttachment)
class RequestAttachmentAdmin(admin.ModelAdmin):
    list_display = ("service_request", "file", "uploaded_by", "uploaded_at")
    readonly_fields = ("uploaded_at",)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("service_request", "technician", "start_at", "end_at", "status")
    list_filter = ("status", "start_at")

@admin.register(Cancellation)
class CancellationAdmin(admin.ModelAdmin):
    list_display = ("service_request", "cancelled_by", "reason", "created_at")
    readonly_fields = ("created_at",)

@admin.register(ServiceHistory)
class ServiceHistoryAdmin(admin.ModelAdmin):
    list_display = ("service_request", "actor", "action", "created_at")
    readonly_fields = ("service_request", "actor", "action", "previous_value", "new_value", "description", "created_at")
