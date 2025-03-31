# myproject/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expense_tracker.settings")

app = Celery("expense_tracker")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Optionally, you can add the result backend here:
# For Redis:
app.conf.result_backend = "redis://localhost:6379/0"

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
