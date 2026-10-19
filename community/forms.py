
from django import forms
from .models import Category, Comment, Post, Report


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["category", "title", "body"]
        widgets = {
            "category": forms.Select(attrs={"class": "community-input"}),
            "title": forms.TextInput(attrs={
                "class": "community-input",
                "placeholder": "Ej. ¿Cómo puedo mejorar la ventilación de mi casa?",
                "maxlength": 160,
            }),
            "body": forms.Textarea(attrs={
                "class": "community-input",
                "rows": 6,
                "placeholder": "Describe tu pregunta o comparte tu consejo...",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={
                "class": "community-input",
                "rows": 4,
                "placeholder": "Escribe una respuesta respetuosa y útil...",
                "maxlength": 3000,
            }),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "details"]
        widgets = {
            "reason": forms.Select(attrs={"class": "community-input"}),
            "details": forms.Textarea(attrs={
                "class": "community-input",
                "rows": 3,
                "placeholder": "Información adicional (opcional)",
                "maxlength": 1500,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"] = forms.ChoiceField(
            choices=[
                ("spam", "Spam o publicidad no deseada"),
                ("offensive", "Contenido ofensivo"),
                ("misinformation", "Información potencialmente engañosa"),
                ("unsafe", "Consejo potencialmente peligroso"),
                ("other", "Otro motivo"),
            ],
            widget=forms.Select(attrs={"class": "community-input"}),
        )
