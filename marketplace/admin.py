from django.contrib import admin

from .models import Activity, BookingRequest, School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_active")
    list_filter = ("is_active", "city")
    search_fields = ("name", "city")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "school", "sport", "price", "is_featured", "is_active")
    list_filter = ("sport", "school", "is_featured", "is_active")
    search_fields = ("title", "summary", "school__name")
    prepopulated_fields = {"slug": ("title",)}
    list_select_related = ("school",)


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "activity",
        "preferred_date",
        "participants",
        "status",
        "created_at",
    )
    list_filter = ("status", "activity__school", "activity__sport", "preferred_date")
    search_fields = ("full_name", "contact", "activity__title")
    list_editable = ("status",)
    readonly_fields = ("public_id", "created_at", "updated_at")
    date_hierarchy = "created_at"
    list_select_related = ("activity", "activity__school")

