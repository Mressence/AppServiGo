from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    path("registro/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("perfil/", views.profile, name="profile"),
    path("cambiar-password/",auth_views.PasswordChangeView.as_view(template_name="accounts/change_password.html",success_url="/accounts/perfil/"), name="change_password"),
]
