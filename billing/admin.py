from django.contrib import admin
from .models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "service_request", "issued_to", "amount", "issued_at")
    search_fields = ("invoice_number", "issued_to__username", "service_request__id")
    readonly_fields = ("invoice_number", "issued_at")
