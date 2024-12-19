# Generated by Django 5.0.6 on 2024-08-23 00:18

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("thepopwinegdrives", "0007_clientapp"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientapp",
            name="client_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="clientapp",
            name="name",
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
