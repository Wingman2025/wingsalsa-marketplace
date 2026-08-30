from datetime import date, timedelta
from io import StringIO
from tempfile import TemporaryDirectory

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.urls import reverse

from .admin import BookingRequestAdmin
from .models import Activity, BookingRequest, School, Sport


class SeedDemoTests(TestCase):
    def test_seed_demo_preserves_management_changes(self):
        call_command("seed_demo", stdout=StringIO())
        activity = Activity.objects.get(slug="iniciacion-wingfoil")
        activity.is_active = False
        activity.save(update_fields=["is_active"])

        call_command("seed_demo", stdout=StringIO())

        activity.refresh_from_db()
        self.assertFalse(activity.is_active)


class MarketplaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name="WingSalsa", slug="wingsalsa")
        cls.wingfoil = Sport.objects.get(slug="wingfoil")
        cls.kitesurf = Sport.objects.get(slug="kitesurf")
        cls.activity = Activity.objects.create(
            school=cls.school,
            title="Iniciación al wingfoil",
            slug="iniciacion-wingfoil",
            sport=cls.wingfoil,
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
        self.assertNotContains(home, "Desde 90 €")
        self.assertNotContains(catalog, "Desde 90 €")

    def test_activity_price_visibility_is_configurable(self):
        detail_url = self.activity.get_absolute_url()
        for show_price in (False, True):
            with self.subTest(show_price=show_price):
                self.activity.show_price = show_price
                self.activity.save(update_fields=["show_price"])

                for url in (
                    reverse("marketplace:home"),
                    reverse("marketplace:activity_list"),
                    detail_url,
                ):
                    response = self.client.get(url)
                    if show_price:
                        self.assertContains(response, "Desde 90 €")
                    else:
                        self.assertNotContains(response, "Desde 90 €")

    def test_health_checks_database(self):
        response = self.client.get(reverse("marketplace:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_public_pages_expose_installable_pwa(self):
        home = self.client.get(reverse("marketplace:home"))
        service_worker = self.client.get(reverse("marketplace:service_worker"))
        manifest_path = finders.find("manifest.webmanifest")

        self.assertContains(home, 'rel="manifest"')
        self.assertIsNotNone(manifest_path)
        with open(manifest_path, encoding="utf-8") as manifest:
            self.assertIn('"display": "standalone"', manifest.read())
        self.assertEqual(service_worker.status_code, 200)
        self.assertEqual(service_worker["Service-Worker-Allowed"], "/")
        self.assertEqual(service_worker["Cache-Control"], "no-cache")
        self.assertContains(service_worker, 'url.pathname.startsWith("/health/")')
        self.assertContains(service_worker, 'url.pathname.startsWith("/gestion/")')
        self.assertContains(service_worker, 'url.pathname.startsWith("/solicitud/")')
        self.assertContains(service_worker, "if (response.ok)", count=2)

    def test_home_prioritizes_wingsalsa_activities(self):
        other_school = School.objects.create(name="Otra escuela", slug="otra")
        Activity.objects.create(
            school=other_school,
            title="Actividad anterior alfabéticamente",
            slug="actividad-otra",
            sport=self.kitesurf,
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

    def test_booking_link_shows_current_status(self):
        booking = BookingRequest.objects.create(
            activity=self.activity,
            full_name="Ana Pérez",
            contact="ana@example.com",
            preferred_date=date.today() + timedelta(days=3),
            participants=2,
        )
        status_url = reverse(
            "marketplace:booking_success",
            kwargs={"public_id": booking.public_id},
        )

        expected_headings = (
            (BookingRequest.Status.NEW, "Solicitud pendiente"),
            (BookingRequest.Status.CONTACTED, "Contacto iniciado"),
            (BookingRequest.Status.CONFIRMED, "Reserva confirmada"),
            (BookingRequest.Status.CANCELLED, "Solicitud cancelada"),
        )
        for status, heading in expected_headings:
            with self.subTest(status=status):
                booking.status = status
                booking.save(update_fields=["status"])

                response = self.client.get(status_url)
                self.assertContains(response, heading)
                self.assertContains(response, booking.get_status_display())
                self.assertContains(response, self.activity.title)
                self.assertContains(response, self.school.name)
                self.assertIn("no-cache", response.headers["Cache-Control"])

                if status != BookingRequest.Status.NEW:
                    self.assertNotContains(response, "Tu plaza todavía no está confirmada")

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


class ManagementAccessTests(TestCase):
    def test_management_dashboard_requires_staff_login(self):
        dashboard_url = reverse("marketplace:manage_dashboard")

        anonymous_response = self.client.get(dashboard_url)
        self.assertRedirects(
            anonymous_response,
            f'{reverse("marketplace:manage_login")}?next={dashboard_url}',
        )

        user = get_user_model().objects.create_superuser(
            username="jorge",
            email="jorge@example.com",
            password="safe-test-password",
        )
        self.client.force_login(user)

        staff_response = self.client.get(dashboard_url)
        self.assertEqual(staff_response.status_code, 200)
        self.assertContains(staff_response, 'href="/"')
        self.assertContains(staff_response, "Ver web")
        self.assertContains(staff_response, "Resumen de hoy")

    def test_management_login_rejects_non_staff_users(self):
        get_user_model().objects.create_user(
            username="visitor",
            email="visitor@example.com",
            password="safe-test-password",
        )

        response = self.client.post(
            reverse("marketplace:manage_login"),
            {"username": "visitor", "password": "safe-test-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Esta cuenta no tiene acceso al panel de gestión.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_without_booking_permission_cannot_see_student_data(self):
        school = School.objects.create(name="WingSalsa", slug="wingsalsa")
        sport = Sport.objects.get(slug="wingfoil")
        activity = Activity.objects.create(
            school=school,
            title="Iniciación al wingfoil",
            slug="iniciacion-wingfoil",
            sport=sport,
            summary="Primera sesión.",
            description="Descripción.",
            price=90,
        )
        BookingRequest.objects.create(
            activity=activity,
            full_name="Nombre Privado",
            contact="privado@example.com",
            preferred_date=date.today() + timedelta(days=3),
        )
        staff_user = get_user_model().objects.create_user(
            username="limited-staff",
            password="safe-test-password",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        dashboard_response = self.client.get(reverse("marketplace:manage_dashboard"))
        booking_response = self.client.get(reverse("marketplace:manage_booking_list"))

        self.assertEqual(dashboard_response.status_code, 200)
        self.assertNotContains(dashboard_response, "Nombre Privado")
        self.assertNotContains(dashboard_response, "privado@example.com")
        self.assertEqual(booking_response.status_code, 403)


class ManagementWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="jorge",
            email="jorge@example.com",
            password="safe-test-password",
        )
        cls.school = School.objects.create(name="WingSalsa", slug="wingsalsa")
        cls.wingfoil = Sport.objects.get(slug="wingfoil")
        cls.kitesurf = Sport.objects.get(slug="kitesurf")
        cls.activity = Activity.objects.create(
            school=cls.school,
            title="Iniciación al wingfoil",
            slug="iniciacion-wingfoil",
            sport=cls.wingfoil,
            summary="Primera sesión con material incluido.",
            description="Aprende las bases del wingfoil.",
            price=90,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_staff_can_filter_and_update_booking_status(self):
        booking = BookingRequest.objects.create(
            activity=self.activity,
            full_name="Ana Pérez",
            contact="ana@example.com",
            preferred_date=date.today() + timedelta(days=3),
        )
        BookingRequest.objects.create(
            activity=self.activity,
            full_name="Luis García",
            contact="luis@example.com",
            preferred_date=date.today() + timedelta(days=5),
            status=BookingRequest.Status.CANCELLED,
        )

        list_response = self.client.get(
            reverse("marketplace:manage_booking_list"),
            {"status": BookingRequest.Status.NEW, "q": "Ana"},
        )
        self.assertContains(list_response, "Ana Pérez")
        self.assertNotContains(list_response, "Luis García")

        update_response = self.client.post(
            reverse(
                "marketplace:manage_booking_status",
                kwargs={"public_id": booking.public_id},
            ),
            {"status": BookingRequest.Status.CONFIRMED},
        )
        self.assertRedirects(
            update_response,
            reverse(
                "marketplace:manage_booking_detail",
                kwargs={"public_id": booking.public_id},
            ),
        )
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingRequest.Status.CONFIRMED)

    def test_staff_can_register_student_manually(self):
        response = self.client.post(
            reverse("marketplace:manage_booking_create"),
            {
                "activity": self.activity.pk,
                "full_name": "Marta Ruiz",
                "contact": "+34 600 111 222",
                "preferred_date": date.today() + timedelta(days=7),
                "participants": 1,
                "level": "Principiante",
                "notes": "Alta realizada por teléfono.",
                "status": BookingRequest.Status.CONFIRMED,
            },
        )
        booking = BookingRequest.objects.get(full_name="Marta Ruiz")
        self.assertRedirects(
            response,
            reverse(
                "marketplace:manage_booking_detail",
                kwargs={"public_id": booking.public_id},
            ),
        )
        self.assertEqual(booking.status, BookingRequest.Status.CONFIRMED)

    def test_staff_can_create_school_and_activity_with_generated_slugs(self):
        school_response = self.client.post(
            reverse("marketplace:manage_school_create"),
            {
                "name": "Océano Sur",
                "description": "Escuela junto al mar.",
                "city": "Tarifa",
                "is_active": True,
            },
        )
        new_school = School.objects.get(name="Océano Sur")
        self.assertRedirects(school_response, reverse("marketplace:manage_school_list"))
        self.assertEqual(new_school.slug, "oceano-sur")

        activity_response = self.client.post(
            reverse("marketplace:manage_activity_create"),
            {
                "school": new_school.pk,
                "title": "Kitesurf puesta a punto",
                "sport": self.kitesurf.pk,
                "summary": "Recupera sensaciones con una sesión práctica.",
                "description": "Sesión adaptada a tu nivel.",
                "price": "70.00",
                "duration_minutes": 90,
                "level": "Intermedio",
                "equipment_included": False,
                "equipment_details": "Consulta disponibilidad.",
                "location": "Los Lances",
                "is_featured": False,
                "is_active": True,
            },
        )
        activity = Activity.objects.get(title="Kitesurf puesta a punto")
        self.assertRedirects(
            activity_response,
            reverse("marketplace:manage_activity_list"),
        )
        self.assertEqual(activity.slug, "kitesurf-puesta-a-punto")

    def test_staff_can_create_sport_and_assign_it_to_activity(self):
        sport_response = self.client.post(
            reverse("marketplace:manage_sport_create"),
            {"name": "Windsurf", "is_active": True},
        )
        windsurf = Sport.objects.get(name="Windsurf")
        self.assertRedirects(sport_response, reverse("marketplace:manage_sport_list"))
        self.assertEqual(windsurf.slug, "windsurf")

        activity_response = self.client.post(
            reverse("marketplace:manage_activity_create"),
            {
                "school": self.school.pk,
                "title": "Windsurf desde cero",
                "sport": windsurf.pk,
                "summary": "Primeros pasos sobre la tabla.",
                "description": "Aprende las bases del windsurf.",
                "price": "70.00",
                "duration_minutes": 120,
                "level": "Principiante",
                "equipment_included": True,
                "equipment_details": "Material completo.",
                "location": "Los Lances",
                "is_featured": False,
                "is_active": True,
            },
        )
        activity = Activity.objects.get(title="Windsurf desde cero")
        self.assertRedirects(activity_response, reverse("marketplace:manage_activity_list"))
        self.assertEqual(activity.sport, windsurf)

    def test_staff_can_create_activity_without_price(self):
        response = self.client.post(
            reverse("marketplace:manage_activity_create"),
            {
                "school": self.school.pk,
                "title": "Actividad sin precio",
                "sport": self.wingfoil.pk,
                "summary": "Precio pendiente de confirmar.",
                "description": "Actividad disponible bajo consulta.",
                "price": "",
                "duration_minutes": 60,
                "level": "Todos los niveles",
                "equipment_included": False,
                "equipment_details": "",
                "location": "Tarifa",
                "is_featured": False,
                "is_active": True,
            },
        )
        activity = Activity.objects.get(title="Actividad sin precio")
        self.assertRedirects(response, reverse("marketplace:manage_activity_list"))
        self.assertIsNone(activity.price)

    def test_staff_can_upload_activity_image_shown_on_home(self):
        image = SimpleUploadedFile(
            "wingfoil.gif",
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse("marketplace:manage_activity_create"),
                {
                    "school": self.school.pk,
                    "title": "Wingfoil con imagen",
                    "sport": self.wingfoil.pk,
                    "summary": "Actividad con portada propia.",
                    "description": "Descripción de la actividad.",
                    "image": image,
                    "price": "80.00",
                    "duration_minutes": 90,
                    "level": "Principiante",
                    "equipment_included": True,
                    "equipment_details": "Material completo.",
                    "location": "Valdevaqueros",
                    "is_featured": True,
                    "is_active": True,
                },
            )
            activity = Activity.objects.get(title="Wingfoil con imagen")
            self.assertRedirects(response, reverse("marketplace:manage_activity_list"))
            self.assertTrue(activity.image.name.startswith("activities/wingfoil"))
            self.assertContains(self.client.get(reverse("marketplace:home")), activity.image.url)
            self.assertContains(self.client.get(activity.get_absolute_url()), activity.image.url)
            with override_settings(DEBUG=False):
                image_response = self.client.get(activity.image.url)
                self.assertEqual(image_response.status_code, 200)
                image_response.close()

    def test_editing_activity_preserves_slug_and_can_hide_it(self):
        response = self.client.post(
            reverse("marketplace:manage_activity_edit", kwargs={"pk": self.activity.pk}),
            {
                "school": self.school.pk,
                "title": "Wingfoil iniciación actualizada",
                "sport": self.wingfoil.pk,
                "summary": "Una descripción actualizada para la actividad.",
                "description": "Contenido actualizado.",
                "price": "95.00",
                "duration_minutes": 120,
                "level": "Principiante",
                "equipment_included": True,
                "equipment_details": "Material completo.",
                "location": "Valdevaqueros",
                "is_featured": True,
                "is_active": False,
            },
        )

        self.assertRedirects(response, reverse("marketplace:manage_activity_list"))
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.slug, "iniciacion-wingfoil")
        self.assertEqual(self.activity.title, "Wingfoil iniciación actualizada")
        self.assertFalse(self.activity.is_active)
