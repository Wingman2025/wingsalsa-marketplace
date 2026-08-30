import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class School(models.Model):
    name = models.CharField("nombre", max_length=140)
    slug = models.SlugField(unique=True)
    description = models.TextField("descripción", blank=True)
    city = models.CharField("ciudad", max_length=100, default="Tarifa")
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "escuela"
        verbose_name_plural = "escuelas"

    def __str__(self):
        return self.name


class Sport(models.Model):
    name = models.CharField("nombre", max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "deporte"
        verbose_name_plural = "deportes"

    def __str__(self):
        return self.name


class Activity(models.Model):
    school = models.ForeignKey(
        School,
        verbose_name="escuela",
        related_name="activities",
        on_delete=models.PROTECT,
    )
    sport = models.ForeignKey(
        Sport,
        verbose_name="deporte",
        related_name="activities",
        on_delete=models.PROTECT,
    )
    title = models.CharField("título", max_length=160)
    slug = models.SlugField(unique=True)
    summary = models.CharField("resumen", max_length=220)
    description = models.TextField("descripción")
    image = models.ImageField(
        "imagen de portada",
        upload_to="activities/",
        blank=True,
    )
    price = models.DecimalField(
        "precio orientativo",
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )
    show_price = models.BooleanField("mostrar precio en la web", default=False)
    duration_minutes = models.PositiveIntegerField("duración en minutos", default=60)
    level = models.CharField("nivel", max_length=100, default="Todos los niveles")
    equipment_included = models.BooleanField("material incluido", default=False)
    equipment_details = models.CharField("detalle del material", max_length=180, blank=True)
    location = models.CharField("ubicación", max_length=160, default="Tarifa")
    is_featured = models.BooleanField("destacada", default=False)
    is_active = models.BooleanField("activa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sport__name", "title"]
        verbose_name = "actividad"
        verbose_name_plural = "actividades"

    def __str__(self):
        return f"{self.title} · {self.school.name}"

    def get_absolute_url(self):
        return reverse("marketplace:activity_detail", kwargs={"slug": self.slug})


class BookingRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Nueva"
        CONTACTED = "contacted", "Contactada"
        CONFIRMED = "confirmed", "Confirmada"
        CANCELLED = "cancelled", "Cancelada"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    activity = models.ForeignKey(
        Activity,
        verbose_name="actividad",
        related_name="booking_requests",
        on_delete=models.PROTECT,
    )
    full_name = models.CharField("nombre completo", max_length=140)
    contact = models.CharField("email o teléfono", max_length=160)
    preferred_date = models.DateField("fecha preferida")
    participants = models.PositiveSmallIntegerField(
        "participantes",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
    )
    level = models.CharField("nivel", max_length=100, blank=True)
    notes = models.TextField("comentario", blank=True)
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    created_at = models.DateTimeField("creada", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "solicitud de reserva"
        verbose_name_plural = "solicitudes de reserva"

    def __str__(self):
        return f"{self.full_name} · {self.activity.title}"

