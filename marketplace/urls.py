from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import StaffAuthenticationForm


app_name = "marketplace"

urlpatterns = [
    path("health/", views.health, name="health"),
    path(
        "gestion/acceso/",
        auth_views.LoginView.as_view(
            template_name="marketplace/manage/login.html",
            authentication_form=StaffAuthenticationForm,
            next_page="marketplace:manage_dashboard",
        ),
        name="manage_login",
    ),
    path(
        "gestion/salir/",
        auth_views.LogoutView.as_view(next_page="marketplace:manage_login"),
        name="manage_logout",
    ),
    path("gestion/", views.manage_dashboard, name="manage_dashboard"),
    path("gestion/reservas/", views.manage_booking_list, name="manage_booking_list"),
    path(
        "gestion/reservas/nueva/",
        views.manage_booking_create,
        name="manage_booking_create",
    ),
    path(
        "gestion/reservas/<uuid:public_id>/",
        views.manage_booking_detail,
        name="manage_booking_detail",
    ),
    path(
        "gestion/reservas/<uuid:public_id>/estado/",
        views.manage_booking_status,
        name="manage_booking_status",
    ),
    path("gestion/escuelas/", views.manage_school_list, name="manage_school_list"),
    path(
        "gestion/escuelas/nueva/",
        views.manage_school_create,
        name="manage_school_create",
    ),
    path(
        "gestion/escuelas/<int:pk>/editar/",
        views.manage_school_edit,
        name="manage_school_edit",
    ),
    path(
        "gestion/actividades/",
        views.manage_activity_list,
        name="manage_activity_list",
    ),
    path(
        "gestion/actividades/nueva/",
        views.manage_activity_create,
        name="manage_activity_create",
    ),
    path(
        "gestion/actividades/<int:pk>/editar/",
        views.manage_activity_edit,
        name="manage_activity_edit",
    ),
    path("", views.home, name="home"),
    path("actividades/", views.activity_list, name="activity_list"),
    path("actividades/<slug:slug>/", views.activity_detail, name="activity_detail"),
    path("solicitud/<uuid:public_id>/enviada/", views.booking_success, name="booking_success"),
]
