# Generated by Django 5.1.3 on 2025-02-12 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wallets", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="interwallettransaction",
            name="date",
        ),
        migrations.AddField(
            model_name="interwallettransaction",
            name="date_time",
            field=models.DateTimeField(default="2025-02-20"),
            preserve_default=False,
        ),
    ]
