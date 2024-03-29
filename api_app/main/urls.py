from django.urls import include, path
from .views import *
from .views_folder import errors_views, orders_views

urlpatterns = [
    path('', index, name='index'),
    path('get_code', get_code, name='get_code'),
    path('get_authorization_code', get_authorization_code, name='get_authorization_code'),
    path('get_access_token/<str:authorization_code>', get_access_token, name='get_access_token'),
    path('post_product', post_product, name='post_product'),
    path('get_orders', orders_views.get_orders, name='get_orders'),
    path('get_order_details/<uuid:id>', orders_views.get_order_details, name='get_order_details'),
    path('change_status/<uuid:id>', orders_views.change_status, name='change_status'),
    path('invalid_token', errors_views.invalid_token, name='invalid_token'),
] 