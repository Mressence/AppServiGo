from django.urls import path
from . import views

app_name = "technicians"

urlpatterns = [
    path("perfil/", views.profile, name="profile"),
    path("solicitud/", views.application, name="application"),
    path("solicitud/estado/", views.application_status, name="application_status"),
    path("perfil/<int:pk>/",views.public_profile,name="public_profile",),
    path("resena/solicitud/<int:request_id>/",views.create_review,name="create_review",),
]
