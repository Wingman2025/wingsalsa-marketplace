import django.db.models.deletion
from django.db import migrations, models


INITIAL_SPORTS = {
    "wingfoil": "Wingfoil",
    "kitesurf": "Kitesurf",
    "yoga": "Yoga",
    "volley": "Vóley",
    "other": "Otro",
}


def migrate_sports(apps, schema_editor):
    Activity = apps.get_model("marketplace", "Activity")
    Sport = apps.get_model("marketplace", "Sport")
    sport_codes = Activity.objects.values_list("sport_code", flat=True).distinct()
    sports = {}
    for slug in {*INITIAL_SPORTS, *sport_codes}:
        name = INITIAL_SPORTS.get(slug, slug.replace("-", " ").title())
        sports[slug] = Sport.objects.create(slug=slug, name=name)
    for activity in Activity.objects.all():
        activity.sport = sports[activity.sport_code]
        activity.save(update_fields=["sport"])


def restore_sport_codes(apps, schema_editor):
    Activity = apps.get_model("marketplace", "Activity")
    for activity in Activity.objects.select_related("sport"):
        activity.sport_code = activity.sport.slug
        activity.save(update_fields=["sport_code"])


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Sport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="nombre")),
                ("slug", models.SlugField(unique=True)),
                ("is_active", models.BooleanField(default=True, verbose_name="activo")),
            ],
            options={
                "verbose_name": "deporte",
                "verbose_name_plural": "deportes",
                "ordering": ["name"],
            },
        ),
        migrations.RenameField(
            model_name="activity",
            old_name="sport",
            new_name="sport_code",
        ),
        migrations.AddField(
            model_name="activity",
            name="sport",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="activities",
                to="marketplace.sport",
                verbose_name="deporte",
            ),
        ),
        migrations.RunPython(migrate_sports, restore_sport_codes),
        migrations.AlterField(
            model_name="activity",
            name="sport",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="activities",
                to="marketplace.sport",
                verbose_name="deporte",
            ),
        ),
        migrations.RemoveField(
            model_name="activity",
            name="sport_code",
        ),
        migrations.AlterModelOptions(
            name="activity",
            options={
                "ordering": ["sport__name", "title"],
                "verbose_name": "actividad",
                "verbose_name_plural": "actividades",
            },
        ),
    ]