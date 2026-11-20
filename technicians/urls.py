from django.urls import path
from . import views

app_name = "technicians"
urlpatterns = [
    path("perfil/", views.profile, name="profile"),
    path("solicitud/", views.application, name="application"),
    path("solicitud/estado/", views.application_status, name="application_status"),
    path("perfil/<int:pk>/", views.public_profile, name="public_profile"),
    path("perfil/<int:pk>/calendario/", views.public_technician_calendar, name="public_calendar"),
    path("resena/solicitud/<int:request_id>/", views.create_review, name="create_review"),
    path("disponibilidad/", views.availability_manage, name="availability"),
    path("disponibilidad/<int:pk>/eliminar/", views.availability_delete, name="availability_delete"),
    path("disponibilidad/bloqueo/", views.availability_exception_create, name="availability_exception_create"),
    path("disponibilidad/bloqueo/<int:pk>/eliminar/", views.availability_exception_delete, name="availability_exception_delete"),
    path("calendario/", views.technician_calendar, name="calendar"),
    path("calendario/eventos/", views.calendar_events, name="calendar_events"),
    path("disponibilidad/horarios/", views.availability_slots, name="availability_slots"),
]
