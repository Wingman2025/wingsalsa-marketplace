from django.contrib import admin
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve


admin.site.site_header = "Wingsalsa MarketPlace"
admin.site.site_title = "Administración"
admin.site.index_title = "Gestión de reservas"


def serve_media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("marketplace.urls")),
    re_path(
        r"^media/(?P<path>.*)$",
        serve_media,
    ),
]

