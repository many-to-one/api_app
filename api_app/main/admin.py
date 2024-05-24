from django.contrib import admin
from users.models import CustomUser  # Import your CustomUser model
from .models import *

# Register the CustomUser model with the admin site
admin.site.register(CustomUser)
admin.site.register(Allegro)
admin.site.register(Secret)
admin.site.register(Address)