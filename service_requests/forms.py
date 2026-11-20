from django import forms
from accounts.models import User
from catalog.models import ServiceType
from technicians.models import TechnicianProfile
from .models import ServiceRequest, Quotation, Appointment, Cancellation


FIELD_CLASS = "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 focus:border-emerald-500 focus:outline-none"


class ServiceRequestForm(forms.ModelForm):
    technician = forms.ModelChoiceField(
        queryset=User.objects.none(), label="Técnico seleccionado",
        empty_label="Selecciona un técnico", required=True,
    )

    class Meta:
        model = ServiceRequest
        fields = ["service_type", "description", "address", "preferred_date"]
        labels = {
            "service_type": "Servicio solicitado",
            "description": "Explica qué trabajo necesitas",
            "address": "Dirección donde se realizará el servicio",
            "preferred_date": "Fecha seleccionada",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Describe el problema, qué necesitas y cualquier detalle importante."}),
            "address": forms.Textarea(attrs={"rows": 3, "placeholder": "Provincia, distrito, corregimiento y referencias."}),
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        initial_technician = kwargs.pop("initial_technician", None)
        initial_service = kwargs.pop("initial_service", None)
        super().__init__(*args, **kwargs)
        self.fields["service_type"].queryset = ServiceType.objects.filter(active=True, category__active=True).select_related("category")
        profiles = TechnicianProfile.objects.filter(
            status=TechnicianProfile.Status.APROBADO,
            category__active=True,
            user__is_active=True,
            user__role=User.Role.TECNICO,
        ).select_related("user", "category")
        self.fields["technician"].queryset = User.objects.filter(
            pk__in=profiles.values("user_id")
        ).order_by("first_name", "username")
        if initial_technician:
            # When a client arrives from a technician's public calendar,
            # keep the request bound to that exact professional.
            self.fields["technician"].queryset = User.objects.filter(pk=initial_technician.pk)
            self.fields["technician"].initial = initial_technician
        if initial_service:
            self.fields["service_type"].initial = initial_service
        for field in self.fields.values():
            field.widget.attrs["class"] = FIELD_CLASS

    def clean(self):
        cleaned = super().clean()
        service = cleaned.get("service_type")
        technician = cleaned.get("technician")
        if service and technician:
            profile = getattr(technician, "technician_profile", None)
            if not profile or profile.status != TechnicianProfile.Status.APROBADO:
                self.add_error("technician", "El técnico seleccionado no está aprobado.")
            elif profile.category_id != service.category_id:
                self.add_error("technician", "El técnico no pertenece a la categoría de este servicio.")
        return cleaned


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ["amount", "details", "estimated_days"]
        labels = {"amount": "Precio total (B/.)", "details": "Detalle y condiciones", "estimated_days": "Duración estimada (días)"}
        widgets = {"amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
                   "details": forms.Textarea(attrs={"rows": 5}), "estimated_days": forms.NumberInput(attrs={"min": 1})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = FIELD_CLASS

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


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["start_at", "end_at", "notes"]
        widgets = {"start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
                   "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
                   "notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = FIELD_CLASS

    def clean(self):
        data = super().clean()
        if data.get("start_at") and data.get("end_at") and data["start_at"] >= data["end_at"]:
            raise forms.ValidationError("La hora final debe ser posterior a la inicial.")
        return data


class CancellationForm(forms.ModelForm):
    class Meta:
        model = Cancellation
        fields = ["reason"]
        widgets = {"reason": forms.Textarea(attrs={"rows": 4, "placeholder": "Explica brevemente por qué cancelas."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].widget.attrs["class"] = FIELD_CLASS
