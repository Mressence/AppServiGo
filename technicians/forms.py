from django import forms

from .models import TechnicianProfile


class TechnicianApplicationForm(forms.ModelForm):

    class Meta:
        model = TechnicianProfile

        fields = [
            "professional_title",
            "description",
            "experience",
            "phone",
            "identity_document",
            "professional_document",
            "additional_document",
        ]

        widgets = {
            "professional_title": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),

            "description": forms.Textarea(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                "rows": 5
            }),

            "experience": forms.NumberInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                "min": 0
            }),

            "phone": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),
        }