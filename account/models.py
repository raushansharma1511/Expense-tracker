import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


# Create your models here.
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(unique=True, blank=False, null=False)
    name = models.CharField(max_length=255, blank=False, null=False)
    phone = models.CharField(max_length=15, blank=True)

    REQUIRED_FIELDS = ["email", "name"]
    EMAIL_FIELD = "email"

    def __str__(self):
        return self.username


class ActiveAccessToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    access_token = models.CharField(max_length=500, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.user.username}"
