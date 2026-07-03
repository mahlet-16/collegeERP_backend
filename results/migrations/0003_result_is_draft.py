from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("results", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="result",
            name="is_draft",
            field=models.BooleanField(default=False),
        ),
    ]
