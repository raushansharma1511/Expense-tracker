# Generated by Django 5.1.3 on 2025-02-11 12:19

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0002_alter_user_phone_no"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="phone_no",
        ),
        migrations.AddField(
            model_name="user",
            name="phone_number",
            field=models.CharField(
                blank=True,
                max_length=13,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        "^\\+91\\d{10}$",
                        "Enter a valid phone number in the format: +91XXXXXXXXXX.",
                    )
                ],
            ),
        ),
    ]
