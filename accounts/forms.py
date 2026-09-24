from django import forms
from django.contrib.auth.forms import UserCreationForm
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
