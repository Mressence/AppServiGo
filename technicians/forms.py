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
