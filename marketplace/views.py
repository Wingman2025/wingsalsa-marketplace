from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.db import connection
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import (
    BookingRequestForm,
    BookingStatusForm,
    ManagementActivityForm,
    ManagementBookingForm,
    ManagementSchoolForm,
    ManagementSportForm,
)
from .models import Activity, BookingRequest, School, Sport


def service_worker(request):
    response = render(request, "service-worker.js", content_type="application/javascript")
    response["Cache-Control"] = "no-cache"
    response["Service-Worker-Allowed"] = "/"
    return response


def offline(request):
    return render(request, "offline.html")


def health(request):
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"status": "unhealthy"}, status=503)
    return JsonResponse({"status": "ok"})


def active_activities():
    return Activity.objects.filter(
        is_active=True,
        school__is_active=True,
        sport__is_active=True,
    ).select_related("school", "sport")


def home(request):
    wingsalsa_first = Case(
        When(school__slug="wingsalsa", then=Value(0)),
        default=Value(1),
        output_field=IntegerField(),
    )
    featured = list(
        active_activities()
        .filter(is_featured=True)
        .annotate(school_priority=wingsalsa_first)
        .order_by("school_priority", "title")[:6]
    )
    if not featured:
        featured = list(
            active_activities()
            .annotate(school_priority=wingsalsa_first)
            .order_by("school_priority", "title")[:6]
        )
    return render(request, "marketplace/home.html", {"activities": featured})


def activity_list(request):
    activities = active_activities()
    sport = request.GET.get("sport", "").strip()
    school = request.GET.get("school", "").strip()
    query = request.GET.get("q", "").strip()

    if sport:
        activities = activities.filter(sport__slug=sport)
    if school:
        activities = activities.filter(school__slug=school)
    if query:
        activities = activities.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(location__icontains=query)
        )

    context = {
        "activities": activities,
        "sports": Sport.objects.filter(is_active=True),
        "schools": School.objects.filter(is_active=True),
        "selected_sport": sport,
        "selected_school": school,
        "query": query,
    }
    return render(request, "marketplace/activity_list.html", context)


def activity_detail(request, slug):
    activity = get_object_or_404(active_activities(), slug=slug)
    form = BookingRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.activity = activity
        booking.save()
        return redirect("marketplace:booking_success", public_id=booking.public_id)
    return render(
        request,
        "marketplace/activity_detail.html",
        {"activity": activity, "form": form},
    )


@never_cache
def booking_success(request, public_id):
    booking = get_object_or_404(
        BookingRequest.objects.select_related("activity", "activity__school"),
        public_id=public_id,
    )
    return render(request, "marketplace/booking_success.html", {"booking": booking})


@staff_member_required(login_url="marketplace:manage_login")
def manage_dashboard(request):
    can_view_bookings = request.user.has_perm("marketplace.view_bookingrequest")
    can_view_activities = request.user.has_perm("marketplace.view_activity")
    bookings = (
        BookingRequest.objects.select_related("activity", "activity__school")
        if can_view_bookings
        else BookingRequest.objects.none()
    )
    context = {
        "new_count": bookings.filter(status=BookingRequest.Status.NEW).count(),
        "contacted_count": bookings.filter(status=BookingRequest.Status.CONTACTED).count(),
        "confirmed_count": bookings.filter(status=BookingRequest.Status.CONFIRMED).count(),
        "active_activity_count": active_activities().count() if can_view_activities else 0,
        "recent_bookings": bookings[:8],
    }
    return render(request, "marketplace/manage/dashboard.html", context)


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.view_bookingrequest", raise_exception=True)
def manage_booking_list(request):
    all_bookings = BookingRequest.objects.select_related("activity", "activity__school")
    bookings = all_bookings
    selected_status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    selected_school = request.GET.get("school", "").strip()
    selected_activity = request.GET.get("activity", "").strip()
    date_from = parse_date(request.GET.get("date_from", ""))

    valid_statuses = {value for value, _ in BookingRequest.Status.choices}
    if selected_status in valid_statuses:
        bookings = bookings.filter(status=selected_status)
    if query:
        bookings = bookings.filter(
            Q(full_name__icontains=query)
            | Q(contact__icontains=query)
            | Q(activity__title__icontains=query)
            | Q(activity__school__name__icontains=query)
        )
    if selected_school.isdigit():
        bookings = bookings.filter(activity__school_id=selected_school)
    if selected_activity.isdigit():
        bookings = bookings.filter(activity_id=selected_activity)
    if date_from:
        bookings = bookings.filter(preferred_date__gte=date_from)

    paginator = Paginator(bookings, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    context = {
        "page_obj": page_obj,
        "booking_count": paginator.count,
        "status_options": [
            {
                "value": value,
                "label": label,
                "count": all_bookings.filter(status=value).count(),
            }
            for value, label in BookingRequest.Status.choices
        ],
        "all_count": all_bookings.count(),
        "schools": School.objects.order_by("name"),
        "activities": Activity.objects.select_related("school").order_by("title"),
        "selected_status": selected_status,
        "selected_school": selected_school,
        "selected_activity": selected_activity,
        "query": query,
        "date_from": request.GET.get("date_from", ""),
        "querystring": query_params.urlencode(),
    }
    return render(request, "marketplace/manage/booking_list.html", context)


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.view_bookingrequest", raise_exception=True)
def manage_booking_detail(request, public_id):
    booking = get_object_or_404(
        BookingRequest.objects.select_related("activity", "activity__school"),
        public_id=public_id,
    )
    return render(
        request,
        "marketplace/manage/booking_detail.html",
        {"booking": booking, "status_choices": BookingRequest.Status.choices},
    )


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.add_bookingrequest", raise_exception=True)
def manage_booking_create(request):
    form = ManagementBookingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        booking = form.save()
        messages.success(request, "La reserva se ha registrado correctamente.")
        return redirect("marketplace:manage_booking_detail", public_id=booking.public_id)
    return render(
        request,
        "marketplace/manage/booking_form.html",
        {"form": form},
    )


@require_POST
@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.change_bookingrequest", raise_exception=True)
def manage_booking_status(request, public_id):
    booking = get_object_or_404(BookingRequest, public_id=public_id)
    form = BookingStatusForm(request.POST, instance=booking)
    if form.is_valid():
        form.save()
        messages.success(request, f"Estado actualizado a {booking.get_status_display()}.")
    else:
        messages.error(request, "No se pudo actualizar el estado.")
    return redirect("marketplace:manage_booking_detail", public_id=booking.public_id)


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.view_school", raise_exception=True)
def manage_school_list(request):
    schools = School.objects.annotate(activity_count=Count("activities"))
    query = request.GET.get("q", "").strip()
    visibility = request.GET.get("visibility", "").strip()
    if query:
        schools = schools.filter(Q(name__icontains=query) | Q(city__icontains=query))
    if visibility == "active":
        schools = schools.filter(is_active=True)
    elif visibility == "inactive":
        schools = schools.filter(is_active=False)
    return render(
        request,
        "marketplace/manage/school_list.html",
        {"schools": schools, "query": query, "visibility": visibility},
    )


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.add_school", raise_exception=True)
def manage_school_create(request):
    form = ManagementSchoolForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La escuela se ha creado correctamente.")
        return redirect("marketplace:manage_school_list")
    return render(
        request,
        "marketplace/manage/entity_form.html",
        {
            "form": form,
            "title": "Nueva escuela",
            "kicker": "Catálogo",
            "intro": "Añade la información básica de la escuela.",
            "submit_label": "Guardar escuela",
            "cancel_url": reverse("marketplace:manage_school_list"),
        },
    )


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.change_school", raise_exception=True)
def manage_school_edit(request, pk):
    school = get_object_or_404(School, pk=pk)
    form = ManagementSchoolForm(request.POST or None, instance=school)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Los cambios de la escuela se han guardado.")
        return redirect("marketplace:manage_school_list")
    return render(
        request,
        "marketplace/manage/entity_form.html",
        {
            "form": form,
            "title": school.name,
            "kicker": "Editar escuela",
            "intro": "Actualiza sus datos o cambia su visibilidad pública.",
            "submit_label": "Guardar cambios",
            "cancel_url": reverse("marketplace:manage_school_list"),
        },
    )


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.view_sport", raise_exception=True)
def manage_sport_list(request):
    sports = Sport.objects.annotate(activity_count=Count("activities"))
    query = request.GET.get("q", "").strip()
    visibility = request.GET.get("visibility", "").strip()
    if query:
        sports = sports.filter(name__icontains=query)
    if visibility == "active":
        sports = sports.filter(is_active=True)
    elif visibility == "inactive":
        sports = sports.filter(is_active=False)
    return render(
        request,
        "marketplace/manage/sport_list.html",
        {"sports": sports, "query": query, "visibility": visibility},
    )


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.add_sport", raise_exception=True)
def manage_sport_create(request):
    form = ManagementSportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "El deporte se ha creado correctamente.")
        return redirect("marketplace:manage_sport_list")
    return render(
        request,
        "marketplace/manage/entity_form.html",
        {
            "form": form,
            "title": "Nuevo deporte",
            "kicker": "Catálogo",
            "intro": "Añade una disciplina para asignarla a las actividades.",
            "submit_label": "Guardar deporte",
            "cancel_url": reverse("marketplace:manage_sport_list"),
        },
    )


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.change_sport", raise_exception=True)
def manage_sport_edit(request, pk):
    sport = get_object_or_404(Sport, pk=pk)
    form = ManagementSportForm(request.POST or None, instance=sport)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Los cambios del deporte se han guardado.")
        return redirect("marketplace:manage_sport_list")
    return render(
        request,
        "marketplace/manage/entity_form.html",
        {
            "form": form,
            "title": sport.name,
            "kicker": "Editar deporte",
            "intro": "Actualiza el nombre o su disponibilidad para nuevas actividades.",
            "submit_label": "Guardar cambios",
            "cancel_url": reverse("marketplace:manage_sport_list"),
        },
    )


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.view_activity", raise_exception=True)
def manage_activity_list(request):
    activities = Activity.objects.select_related("school", "sport")
    query = request.GET.get("q", "").strip()
    selected_school = request.GET.get("school", "").strip()
    selected_sport = request.GET.get("sport", "").strip()
    visibility = request.GET.get("visibility", "").strip()
    if query:
        activities = activities.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(location__icontains=query)
        )
    if selected_school.isdigit():
        activities = activities.filter(school_id=selected_school)
    if selected_sport:
        activities = activities.filter(sport__slug=selected_sport)
    if visibility == "active":
        activities = activities.filter(is_active=True, school__is_active=True)
    elif visibility == "inactive":
        activities = activities.filter(Q(is_active=False) | Q(school__is_active=False))
    return render(
        request,
        "marketplace/manage/activity_list.html",
        {
            "activities": activities,
            "schools": School.objects.order_by("name"),
            "sports": Sport.objects.order_by("name"),
            "query": query,
            "selected_school": selected_school,
            "selected_sport": selected_sport,
            "visibility": visibility,
        },
    )


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.add_activity", raise_exception=True)
def manage_activity_create(request):
    form = ManagementActivityForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La actividad se ha creado correctamente.")
        return redirect("marketplace:manage_activity_list")
    return render(
        request,
        "marketplace/manage/entity_form.html",
        {
            "form": form,
            "title": "Nueva actividad",
            "kicker": "Catálogo",
            "intro": "Publica una nueva clase con toda la información necesaria.",
            "submit_label": "Guardar actividad",
            "cancel_url": reverse("marketplace:manage_activity_list"),
        },
    )


@staff_member_required(login_url="marketplace:manage_login")
@permission_required("marketplace.change_activity", raise_exception=True)
def manage_activity_edit(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    form = ManagementActivityForm(request.POST or None, request.FILES or None, instance=activity)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Los cambios de la actividad se han guardado.")
        return redirect("marketplace:manage_activity_list")
    return render(
        request,
        "marketplace/manage/entity_form.html",
        {
            "form": form,
            "title": activity.title,
            "kicker": "Editar actividad",
            "intro": "Actualiza la oferta o cambia su visibilidad pública.",
            "submit_label": "Guardar cambios",
            "cancel_url": reverse("marketplace:manage_activity_list"),
            "preview_url": activity.get_absolute_url(),
        },
    )
