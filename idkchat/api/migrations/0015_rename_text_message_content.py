# Generated by Django 4.2.1 on 2023-05-28 16:01

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0014_dialog_key_1_dialog_key_2"),
    ]

    operations = [
        migrations.RenameField(
            model_name="message",
            old_name="text",
            new_name="content",
        ),
    ]