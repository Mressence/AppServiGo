from django.urls import path
from . import views

app_name = "service_requests"
urlpatterns = [
    path("", views.request_list, name="list"),
    path("nueva/", views.request_create, name="create"),
    path("<int:pk>/", views.request_detail, name="detail"),
    path("<int:pk>/cotizar/", views.quotation_create, name="quotation_create"),
    path("<int:pk>/cita/nueva/", views.appointment_create, name="appointment_create"),
    path("citas/", views.appointment_list, name="appointment_list"),
    path("cita/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("cita/<int:pk>/reprogramar/", views.appointment_reschedule, name="appointment_reschedule"),
    path("cita/<int:pk>/cancelar/", views.appointment_cancel, name="appointment_cancel"),
    path("cita/<int:pk>/completar/", views.appointment_finish, name="appointment_finish"),
    path("cita/<int:pk>/confirmar/", views.appointment_confirm, name="appointment_confirm"),
]
