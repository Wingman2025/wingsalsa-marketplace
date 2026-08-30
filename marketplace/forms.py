from datetime import date

from django import forms

from .models import BookingRequest


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

