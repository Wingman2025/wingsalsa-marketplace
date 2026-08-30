from datetime import date, timedelta

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .admin import BookingRequestAdmin
from .models import Activity, BookingRequest, School


class MarketplaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name="WingSalsa", slug="wingsalsa")
        cls.activity = Activity.objects.create(
            school=cls.school,
            title="Iniciación al wingfoil",
            slug="iniciacion-wingfoil",
            sport=Activity.Sport.WINGFOIL,
            summary="Primera sesión con material incluido.",
            description="Aprende las bases del wingfoil.",
            price=90,
            duration_minutes=120,
            level="Principiante",
            equipment_included=True,
            location="Valdevaqueros",
            is_featured=True,
        )

    def test_home_and_catalog_show_active_activity(self):
        home = self.client.get(reverse("marketplace:home"))
        catalog = self.client.get(reverse("marketplace:activity_list"))
        self.assertContains(home, self.activity.title)
        self.assertContains(catalog, self.activity.title)

    def test_health_checks_database(self):
        response = self.client.get(reverse("marketplace:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_home_prioritizes_wingsalsa_activities(self):
        other_school = School.objects.create(name="Otra escuela", slug="otra")
        Activity.objects.create(
            school=other_school,
            title="Actividad anterior alfabéticamente",
            slug="actividad-otra",
            sport=Activity.Sport.KITESURF,
            summary="Otra actividad destacada.",
            description="Descripción.",
            price=50,
            is_featured=True,
        )
        response = self.client.get(reverse("marketplace:home"))
        content = response.content.decode()
        self.assertLess(content.index(self.activity.title), content.index("Actividad anterior"))

    def test_catalog_filters_by_sport(self):
        response = self.client.get(reverse("marketplace:activity_list"), {"sport": "yoga"})
        self.assertNotContains(response, self.activity.title)
        self.assertContains(response, "No encontramos actividades")

    def test_inactive_activity_is_not_public(self):
        self.activity.is_active = False
        self.activity.save(update_fields=["is_active"])
        response = self.client.get(self.activity.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_guest_can_send_booking_request(self):
        response = self.client.post(
            self.activity.get_absolute_url(),
            {
                "full_name": "Ana Pérez",
                "contact": "ana@example.com",
                "preferred_date": date.today() + timedelta(days=3),
                "participants": 2,
                "level": "Principiante",
                "notes": "Necesitamos material.",
            },
        )
        booking = BookingRequest.objects.get()
        self.assertRedirects(
            response,
            reverse("marketplace:booking_success", kwargs={"public_id": booking.public_id}),
        )
        self.assertEqual(booking.status, BookingRequest.Status.NEW)
        self.assertEqual(booking.activity, self.activity)

    def test_past_date_is_rejected(self):
        response = self.client.post(
            self.activity.get_absolute_url(),
            {
                "full_name": "Ana Pérez",
                "contact": "ana@example.com",
                "preferred_date": date.today() - timedelta(days=1),
                "participants": 1,
            },
        )
        self.assertContains(response, "Elige una fecha de hoy en adelante.")
        self.assertFalse(BookingRequest.objects.exists())

    def test_admin_requires_login_and_supports_status_filter(self):
        response = self.client.get(reverse("admin:marketplace_bookingrequest_changelist"))
        self.assertEqual(response.status_code, 302)
        admin_config = BookingRequestAdmin(BookingRequest, site)
        self.assertIn("status", admin_config.list_filter)
        self.assertIn("status", admin_config.list_editable)

    def test_admin_can_open_booking_list(self):
        user = get_user_model().objects.create_superuser(
            username="jorge",
            email="jorge@example.com",
            password="safe-test-password",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("admin:marketplace_bookingrequest_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solicitudes de reserva")
