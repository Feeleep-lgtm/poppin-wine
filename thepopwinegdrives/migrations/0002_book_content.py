# Generated by Django 5.0.6 on 2024-06-20 02:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("thepopwinegdrives", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="content",
            field=models.TextField(blank=True, null=True),
        ),
    ]
