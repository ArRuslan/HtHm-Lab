# Generated by Django 4.2.1 on 2023-05-24 16:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0009_session_expire_timestamp"),
    ]

    operations = [
        migrations.CreateModel(
            name="Dialog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "user_1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_1",
                        to="api.user",
                    ),
                ),
                (
                    "user_2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_2",
                        to="api.user",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]