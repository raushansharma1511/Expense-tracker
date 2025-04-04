# Generated by Django 5.1.3 on 2025-02-07 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recurring_transactions", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recurringtransaction",
            name="frequency",
            field=models.CharField(
                choices=[
                    ("daily", "Daily"),
                    ("weekly", "Weekly"),
                    ("monthly", "Monthly"),
                    ("yearly", "Yearly"),
                ],
                max_length=10,
            ),
        ),
    ]
