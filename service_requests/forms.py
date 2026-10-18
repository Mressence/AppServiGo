from django import forms
from catalog.models import ServiceType
from .models import ServiceRequest, Quotation


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ["service_type", "description", "address", "preferred_date"]
        labels = {
            "service_type": "Servicio solicitado",
            "description": "Describe lo que necesitas",
            "address": "Dirección donde se realizará el servicio",
            "preferred_date": "Fecha preferida (opcional)",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Explica el trabajo que necesitas, el problema y cualquier detalle útil."}),
            "address": forms.Textarea(attrs={"rows": 3, "placeholder": "Provincia, distrito, corregimiento y referencia."}),
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        initial_service = kwargs.pop("initial_service", None)
        super().__init__(*args, **kwargs)
        self.fields["service_type"].queryset = ServiceType.objects.filter(active=True, category__active=True).select_related("category")
        if initial_service:
            self.fields["service_type"].initial = initial_service
        for field in self.fields.values():
            field.widget.attrs["class"] = "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 focus:border-emerald-500 focus:outline-none"


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ["amount", "details", "estimated_days"]
        labels = {"amount": "Precio total (B/.)", "details": "Alcance y condiciones", "estimated_days": "Duración estimada (días)"}
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "details": forms.Textarea(attrs={"rows": 5, "placeholder": "Incluye materiales, mano de obra y qué cubre el precio."}),
            "estimated_days": forms.NumberInput(attrs={"min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 focus:border-emerald-500 focus:outline-none"

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("El precio debe ser mayor que cero.")
        return amount

    def clean_estimated_days(self):
        days = self.cleaned_data["estimated_days"]
        if days < 1:
            raise forms.ValidationError("La duración debe ser de al menos un día.")
        return days
