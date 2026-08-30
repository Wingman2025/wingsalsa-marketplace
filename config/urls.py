from django.contrib import admin
from django.urls import include, path


admin.site.site_header = "Wingsalsa MarketPlace"
admin.site.site_title = "Administración"
admin.site.index_title = "Gestión de reservas"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("marketplace.urls")),
]

