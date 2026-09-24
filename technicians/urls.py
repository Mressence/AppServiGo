from django.urls import path
from . import views

app_name = "technicians"

urlpatterns = [path("solicitud/",views.technician_application,name="application"),
               path("solicitud/estado/",views.application_status,name="application_status"),

]