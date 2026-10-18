from django.urls import path
from . import views

app_name = "technicians"

urlpatterns = [
    path("perfil/", views.profile, name="profile"),
    path("solicitud/", views.application, name="application"),
    path("solicitud/estado/", views.application_status, name="application_status"),
]
