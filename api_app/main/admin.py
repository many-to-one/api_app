from django.contrib import admin
from users.models import CustomUser  # Import your CustomUser model

# Register the CustomUser model with the admin site
admin.site.register(CustomUser)