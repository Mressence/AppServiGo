from django.urls import path
from . import views

app_name = "notifications"
urlpatterns = [
    path("", views.notification_list, name="list"),
    path("<int:pk>/leer/", views.notification_read, name="read"),
    path("leer-todas/", views.notification_read_all, name="read_all"),
]
