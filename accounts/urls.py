from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("registro/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("perfil/", views.profile, name="profile"),
    path("cambiar-password/", views.ServiGoPasswordChangeView.as_view(), name="change_password"),
]
