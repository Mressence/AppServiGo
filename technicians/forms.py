from django import forms
from .models import TechnicianProfile

class TechnicianProfileForm(forms.ModelForm):
    class Meta:
        model = TechnicianProfile
        fields = ["professional_title", "description", "experience", "phone"]
        labels = {
            "professional_title": "Especialidad / título profesional",
            "description": "Descripción profesional",
            "experience": "Años de experiencia",
            "phone": "Teléfono",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }
