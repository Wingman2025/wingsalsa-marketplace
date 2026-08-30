from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0002_sport_catalog"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activity",
            name="price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
                verbose_name="precio orientativo",
            ),
        ),
    ]