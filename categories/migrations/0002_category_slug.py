# Generated by Django 5.1.3 on 2025-02-12 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="slug",
            field=models.CharField(default="hello", max_length=100),
            preserve_default=False,
        ),
    ]
