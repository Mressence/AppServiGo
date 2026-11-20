from django.urls import path
from . import views

app_name = "billing"
urlpatterns = [
    path("", views.invoice_list, name="list"),
    path("<int:pk>/", views.invoice_detail, name="detail"),
    path("descargar/<int:request_id>/", views.invoice_download, name="download"),
]
