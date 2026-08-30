from datetime import date

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.text import slugify

from .models import Activity, BookingRequest, School


def unique_slug(instance, source):
    model = type(instance)
    max_length = model._meta.get_field("slug").max_length
    root = slugify(source) or model._meta.model_name
    candidate = root[:max_length]
    suffix_number = 2
    existing = model.objects.exclude(pk=instance.pk)
    while existing.filter(slug=candidate).exists():
        suffix = f"-{suffix_number}"
        candidate = f"{root[:max_length - len(suffix)]}{suffix}"
        suffix_number += 1
    return candidate


class StaffAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError(
                "Esta cuenta no tiene acceso al panel de gestión.",
                code="not_staff",
            )


class BookingRequestForm(forms.ModelForm):
    class Meta:
        model = BookingRequest
        fields = [
            "full_name",
            "contact",
            "preferred_date",
            "participants",
            "level",
            "notes",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Tu nombre"}),
            "contact": forms.TextInput(
                attrs={"autocomplete": "email", "placeholder": "Email o teléfono"}
            ),
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "participants": forms.NumberInput(attrs={"min": 1, "max": 20}),
            "level": forms.TextInput(attrs={"placeholder": "Por ejemplo: principiante"}),
            "notes": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Cuéntanos qué necesitas (opcional)"}
            ),
        }
        labels = {
            "full_name": "Nombre",
            "contact": "Email o teléfono",
            "preferred_date": "¿Qué día prefieres?",
            "participants": "Personas",
            "level": "Nivel",
            "notes": "Comentario",
        }

    def clean_preferred_date(self):
        preferred_date = self.cleaned_data["preferred_date"]
        if preferred_date < date.today():
            raise forms.ValidationError("Elige una fecha de hoy en adelante.")
        return preferred_date


class ManagementBookingForm(forms.ModelForm):
    class Meta:
        model = BookingRequest
        fields = [
            "activity",
            "full_name",
            "contact",
            "preferred_date",
            "participants",
            "level",
            "notes",
            "status",
        ]
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "participants": forms.NumberInput(attrs={"min": 1, "max": 20}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "activity": "Actividad",
            "full_name": "Nombre del estudiante",
            "contact": "Email o teléfono",
            "preferred_date": "Fecha",
            "participants": "Personas",
            "level": "Nivel",
            "notes": "Notas internas",
            "status": "Estado inicial",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["activity"].queryset = (
            Activity.objects.filter(is_active=True, school__is_active=True)
            .select_related("school")
            .order_by("school__name", "title")
        )
        self.fields["activity"].empty_label = "Selecciona una actividad"

    def clean_preferred_date(self):
        preferred_date = self.cleaned_data["preferred_date"]
        if preferred_date < date.today():
            raise forms.ValidationError("Elige una fecha de hoy en adelante.")
        return preferred_date


class BookingStatusForm(forms.ModelForm):
    class Meta:
        model = BookingRequest
        fields = ["status"]


class ManagementSchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ["name", "description", "city", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
        labels = {
            "name": "Nombre",
            "description": "Descripción",
            "city": "Ciudad",
            "is_active": "Visible en la web",
        }

    def save(self, commit=True):
        school = super().save(commit=False)
        if not school.slug:
            school.slug = unique_slug(school, school.name)
        if commit:
            school.save()
        return school


class ManagementActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            "school",
            "title",
            "sport",
            "summary",
            "description",
            "price",
            "duration_minutes",
            "level",
            "equipment_included",
            "equipment_details",
            "location",
            "is_featured",
            "is_active",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 2}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "price": forms.NumberInput(attrs={"min": 0, "step": "0.01"}),
            "duration_minutes": forms.NumberInput(attrs={"min": 1}),
        }
        labels = {
            "school": "Escuela",
            "title": "Nombre de la actividad",
            "sport": "Deporte",
            "summary": "Resumen corto",
            "description": "Descripción completa",
            "price": "Precio orientativo (€)",
            "duration_minutes": "Duración (minutos)",
            "level": "Nivel",
            "equipment_included": "Material incluido",
            "equipment_details": "Detalles del material",
            "location": "Ubicación",
            "is_featured": "Destacar en portada",
            "is_active": "Publicada en la web",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["school"].queryset = School.objects.order_by("name")
        self.fields["school"].empty_label = "Selecciona una escuela"
        self.fields["sport"].choices = [("", "Selecciona un deporte"), *Activity.Sport.choices]

    def save(self, commit=True):
        activity = super().save(commit=False)
        if not activity.slug:
            activity.slug = unique_slug(activity, activity.title)
        if commit:
            activity.save()
        return activity

