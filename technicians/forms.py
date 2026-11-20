from pathlib import Path
from django import forms
from .models import TechnicianProfile

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024


class TechnicianApplicationForm(forms.ModelForm):
    class Meta:
        model = TechnicianProfile
        fields = ["professional_title", "description", "experience", "phone", "identity_document", "professional_document", "additional_document"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
        labels = {
            "professional_title": "Especialidad / título profesional",
            "description": "Experiencia y descripción profesional",
            "experience": "Años de experiencia",
            "phone": "Teléfono de contacto",
            "identity_document": "Documento de identidad (PDF, JPG o PNG)",
            "professional_document": "Título o certificación (PDF, JPG o PNG)",
            "additional_document": "Documento adicional (opcional)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "w-full rounded-xl border border-slate-200 bg-white px-4 py-3"
        self.fields["identity_document"].required = not bool(self.instance and self.instance.identity_document)
        self.fields["professional_document"].required = not bool(self.instance and self.instance.professional_document)

    def clean(self):
        cleaned = super().clean()
        for name in ("identity_document", "professional_document", "additional_document"):
            uploaded = cleaned.get(name)
            if uploaded and hasattr(uploaded, "size"):
                extension = Path(uploaded.name).suffix.lower()
                if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
                    self.add_error(name, "Formato no permitido. Usa PDF, JPG, JPEG, PNG o WEBP.")
                if uploaded.size > MAX_DOCUMENT_SIZE:
                    self.add_error(name, "Cada documento debe pesar como máximo 10 MB.")
        return cleaned

from django import forms
from django.db.models import Q
from .models import TechnicianAvailability, AvailabilityException


class TechnicianAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TechnicianAvailability
        fields = ["weekday", "start_time", "end_time", "active"]
        widgets = {"start_time": forms.TimeInput(attrs={"type": "time"}),
                   "end_time": forms.TimeInput(attrs={"type": "time"})}

    def __init__(self, *args, **kwargs):
        self.technician = kwargs.pop("technician", None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "w-full rounded-xl border border-slate-200 px-3 py-2"

    def clean(self):
        data = super().clean()
        start, end, weekday = data.get("start_time"), data.get("end_time"), data.get("weekday")
        if start and end and start >= end:
            raise forms.ValidationError("La hora final debe ser posterior a la inicial.")
        if self.technician and start and end and weekday is not None:
            overlaps = TechnicianAvailability.objects.filter(
                technician=self.technician, weekday=weekday, active=True,
                start_time__lt=end, end_time__gt=start,
            )
            if self.instance.pk:
                overlaps = overlaps.exclude(pk=self.instance.pk)
            if overlaps.exists():
                raise forms.ValidationError("Ese horario se cruza con otro horario que ya configuraste.")
        return data


class AvailabilityExceptionForm(forms.ModelForm):
    class Meta:
        model = AvailabilityException
        fields = ["start_at", "end_at", "reason"]
        widgets = {"start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
                   "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "w-full rounded-xl border border-slate-200 px-3 py-2"

    def clean(self):
        data = super().clean()
        start, end = data.get("start_at"), data.get("end_at")
        if start and end and start >= end:
            raise forms.ValidationError("La fecha final debe ser posterior a la inicial.")
        return data
