from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0003_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendance",
            name="is_draft",
            field=models.BooleanField(default=False),
        ),
    ]
