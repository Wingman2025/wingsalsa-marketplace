from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0003_alter_activity_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="activity",
            name="image",
            field=models.ImageField(blank=True, upload_to="activities/", verbose_name="imagen de portada"),
        ),
    ]