# Generated by Django 5.1.6 on 2025-02-24 22:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sess_admin_portal", "0003_client_sex"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="sex",
            field=models.CharField(
                choices=[("Male", "M"), ("Female", "F")], default="Male", max_length=100
            ),
        ),
    ]
