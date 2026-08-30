from django.core.management.base import BaseCommand

from marketplace.models import Activity, School, Sport


class Command(BaseCommand):
    help = "Crea escuelas y actividades de demostración para el MVP local."

    def handle(self, *args, **options):
        wingsalsa, _ = School.objects.get_or_create(
            slug="wingsalsa",
            defaults={
                "name": "WingSalsa",
                "description": "Escuela local de wingfoil en Tarifa.",
                "city": "Tarifa",
                "is_active": True,
            },
        )
        tarifa_flow, _ = School.objects.get_or_create(
            slug="tarifa-flow",
            defaults={
                "name": "Tarifa Flow",
                "description": "Movimiento y bienestar junto al mar.",
                "city": "Tarifa",
                "is_active": True,
            },
        )
        beach_club, _ = School.objects.get_or_create(
            slug="sur-beach-club",
            defaults={
                "name": "Sur Beach Club",
                "description": "Deporte y comunidad en la playa.",
                "city": "Tarifa",
                "is_active": True,
            },
        )

        sports = {}
        for slug, name in (
            ("wingfoil", "Wingfoil"),
            ("kitesurf", "Kitesurf"),
            ("yoga", "Yoga"),
            ("volley", "Vóley"),
            ("other", "Otro"),
        ):
            sports[slug], _ = Sport.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "is_active": True},
            )

        activities = [
            {
                "school": wingsalsa,
                "slug": "iniciacion-wingfoil",
                "title": "Iniciación al wingfoil",
                "sport": sports["wingfoil"],
                "summary": "Tu primera experiencia con el foil, paso a paso y con material incluido.",
                "description": "Aprende las bases del wingfoil con un instructor local. Empezaremos en tierra, conocerás el material y pasaremos al agua cuando las condiciones sean adecuadas.",
                "price": 90,
                "duration_minutes": 120,
                "level": "Principiante",
                "equipment_included": True,
                "equipment_details": "Tabla, foil, wing, casco y chaleco.",
                "location": "Valdevaqueros",
                "is_featured": True,
                "is_active": True,
            },
            {
                "school": wingsalsa,
                "slug": "progresion-wingfoil",
                "title": "Progresión wingfoil",
                "sport": sports["wingfoil"],
                "summary": "Una sesión enfocada en despegar, mantener el vuelo y ganar control.",
                "description": "Trabajaremos sobre tu punto actual con objetivos concretos y correcciones prácticas. La sesión se adapta a las condiciones y a tu experiencia.",
                "price": 75,
                "duration_minutes": 90,
                "level": "Intermedio",
                "equipment_included": False,
                "equipment_details": "Consulta disponibilidad de material al solicitar.",
                "location": "Tarifa",
                "is_featured": True,
                "is_active": True,
            },
            {
                "school": tarifa_flow,
                "slug": "yoga-frente-al-mar",
                "title": "Yoga frente al mar",
                "sport": sports["yoga"],
                "summary": "Una práctica abierta para empezar el día con movilidad y calma.",
                "description": "Sesión accesible de movilidad, respiración y yoga. No necesitas experiencia previa y puedes consultar disponibilidad de esterilla.",
                "price": 18,
                "duration_minutes": 60,
                "level": "Todos los niveles",
                "equipment_included": False,
                "equipment_details": "Trae tu esterilla o consulta disponibilidad.",
                "location": "Los Lances",
                "is_featured": True,
                "is_active": True,
            },
            {
                "school": beach_club,
                "slug": "volley-playa-abierto",
                "title": "Vóley playa abierto",
                "sport": sports["volley"],
                "summary": "Partido guiado para conocer gente y disfrutar en la arena.",
                "description": "Grupos organizados por nivel con calentamiento y partidos. Puedes apuntarte solo o con amigos.",
                "price": 12,
                "duration_minutes": 90,
                "level": "Todos los niveles",
                "equipment_included": True,
                "equipment_details": "Balones y pista incluidos.",
                "location": "Playa de Los Lances",
                "is_featured": True,
                "is_active": True,
            },
        ]

        for data in activities:
            slug = data.pop("slug")
            Activity.objects.get_or_create(slug=slug, defaults=data)

        self.stdout.write(self.style.SUCCESS("Datos de demostración preparados."))

