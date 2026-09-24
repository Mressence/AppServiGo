from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import User

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, label="Apellido")
    email = forms.EmailField(label="Correo electrónico")
    role = forms.ChoiceField(
        choices=[
            (User.Role.USUARIO, "Usuario"),
            (User.Role.TECNICO, "Técnico"),
        ],
        label="Tipo de cuenta",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "role", "password1", "password2"]
class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "profile_photo",
        ]

        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),

            "last_name": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),

            "email": forms.EmailInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),

            "phone": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),

            "address": forms.Textarea(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3",
                "rows": 3
            }),

            "profile_photo": forms.ClearableFileInput(attrs={
                "class": "w-full rounded-xl border border-slate-300 px-4 py-3"
            }),
        }