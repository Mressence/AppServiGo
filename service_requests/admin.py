from django.contrib import admin
from .models import ServiceRequest, RequestAttachment, Quotation


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
    list_display = ("id", "service_type", "requester", "status", "assigned_technician", "created_at")
    list_filter = ("status", "service_type__category", "created_at")
    search_fields = ("requester__username", "requester__email", "service_type__name", "description")
    readonly_fields = ("created_at", "updated_at")
    inlines = (RequestAttachmentInline, QuotationInline)


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("id", "service_request", "technician", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("service_request__id", "technician__username", "details")


@admin.register(RequestAttachment)
class RequestAttachmentAdmin(admin.ModelAdmin):
    list_display = ("service_request", "file", "uploaded_by", "uploaded_at")
    readonly_fields = ("uploaded_at",)
