from django.urls import path

from . import views


app_name = "marketplace"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("", views.home, name="home"),
    path("actividades/", views.activity_list, name="activity_list"),
    path("actividades/<slug:slug>/", views.activity_detail, name="activity_detail"),
    path("solicitud/<uuid:public_id>/enviada/", views.booking_success, name="booking_success"),
]
