
from django.urls import path
from . import views

app_name = "community"

urlpatterns = [
    path("", views.post_list, name="list"),
    path("nueva/", views.post_create, name="create"),
    path("publicacion/<int:pk>/", views.post_detail, name="detail"),
    path("publicacion/<int:pk>/responder/", views.comment_create, name="comment"),
    path("publicacion/<int:pk>/votar/", views.post_vote, name="vote"),
    path("publicacion/<int:pk>/reportar/", views.post_report, name="report"),
    path("moderacion/", views.moderation, name="moderation"),
    path(
        "moderacion/<str:item_type>/<int:pk>/",
        views.moderate_item,
        name="moderate_item",
    ),
    path(
        "moderacion/reporte/<int:pk>/",
        views.moderate_report,
        name="moderate_report",
    ),
]
