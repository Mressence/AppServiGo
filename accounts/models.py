from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        USUARIO = "USUARIO", "Usuario"
        TECNICO = "TECNICO", "Técnico"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USUARIO)
    phone = models.CharField("Teléfono", max_length=30, blank=True)
    address = models.TextField("Dirección", blank=True)
    profile_photo = models.ImageField("Foto de perfil", upload_to="profile_photos/", blank=True, null=True)

    def __str__(self):
        return self.get_full_name() or self.username
