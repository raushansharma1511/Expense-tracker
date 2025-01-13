from django.contrib import admin
from .models import User, ActiveAccessToken

# Register your models here.
admin.site.register(User)
admin.site.register(ActiveAccessToken)
