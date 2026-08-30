from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0004_activity_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="activity",
            name="show_price",
            field=models.BooleanField(default=False, verbose_name="mostrar precio en la web"),
        ),
    ]