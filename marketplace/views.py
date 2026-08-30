from django.db.models import Case, IntegerField, Q, Value, When
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookingRequestForm
from .models import Activity, BookingRequest, School


def health(request):
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"status": "unhealthy"}, status=503)
    return JsonResponse({"status": "ok"})


def active_activities():
    return Activity.objects.filter(is_active=True, school__is_active=True).select_related("school")


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
        activities = activities.filter(sport=sport)
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
        "sports": Activity.Sport.choices,
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


def booking_success(request, public_id):
    booking = get_object_or_404(
        BookingRequest.objects.select_related("activity", "activity__school"),
        public_id=public_id,
    )
    return render(request, "marketplace/booking_success.html", {"booking": booking})
