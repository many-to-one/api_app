from django.urls import path
from .views import *

urlpatterns = [
    path('register', register, name='register'),
    path('login_user/', login_user, name='login_user'),
    path('logout_user/', logout_user, name='logout_user'),
] 