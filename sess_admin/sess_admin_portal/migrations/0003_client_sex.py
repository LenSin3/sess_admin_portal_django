# Generated by Django 5.1.6 on 2025-02-24 22:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sess_admin_portal", "0002_diagnosis_medicalhistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="sex",
            field=models.CharField(
                choices=[("Male", "M"), ("Female", "F")], default="Male", max_length=100
            ),
        ),
    ]
