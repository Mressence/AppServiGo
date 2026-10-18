from django.urls import path
from . import views

app_name = "service_requests"

urlpatterns = [
    path("", views.request_list, name="list"),
    path("nueva/", views.request_create, name="create"),
    path("<int:pk>/", views.request_detail, name="detail"),
    path("<int:pk>/cotizar/", views.quotation_create, name="quotation_create"),
]
