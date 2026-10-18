from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import User


class StyledFormMixin:
    default_class = "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-800 focus:border-emerald-500 focus:outline-none"

    def style_fields(self):
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{self.default_class} {existing}".strip()


class RegisterForm(StyledFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, label="Apellido")
    email = forms.EmailField(label="Correo electrónico")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.USUARIO
        if commit:
            user.save()
        return user


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "address", "profile_photo"]
        labels = {
            "first_name": "Nombre", "last_name": "Apellido", "email": "Correo electrónico",
            "phone": "Teléfono", "address": "Dirección", "profile_photo": "Foto de perfil",
        }
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo electrónico.")
        return email


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
