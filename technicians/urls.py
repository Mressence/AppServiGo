from django.urls import path
from . import views

app_name = "technicians"

urlpatterns = [
    path("perfil/", views.profile, name="profile"),
]
