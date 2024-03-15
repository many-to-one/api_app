from django.urls import include, path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('get_authorization_code', get_authorization_code, name='get_authorization_code'),
    path('get_access_token', get_access_token, name='get_access_token'),
] 