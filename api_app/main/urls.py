from django.urls import include, path
from .views import *
from .views_folder import errors_views, orders_views, offer_views, accounts_views

urlpatterns = [
    path('', index, name='index'),
    path('success/<str:text>', success, name='success'),
    path('add_account', accounts_views.add_account, name='add_account'),
    # path('get_accounts', orders_views.get_accounts, name='get_accounts'),
    path('get_new_code/<str:name>', get_new_code, name='get_new_code'),
    path('get_new_authorization_code/<str:name>', get_new_authorization_code, name='get_new_authorization_code'),
    path('get_code', get_code, name='get_code'),
    path('get_authorization_code', get_authorization_code, name='get_authorization_code'),
    path('get_access_token/<str:authorization_code>/<str:name>/', get_access_token, name='get_access_token'),
    path('get_refresh_token/<str:authorization_code>', get_refresh_token, name='get_refresh_token'),
    path('post_product', post_product, name='post_product'),
    path('get_orders', orders_views.get_orders, name='get_orders'),
    path('get_order_details/<uuid:id>', orders_views.get_order_details, name='get_order_details'),
    path('change_status/<uuid:id>/<str:name>/', orders_views.change_status, name='change_status'),
    path('invalid_token', errors_views.invalid_token, name='invalid_token'),
    path('get_all_offers/<str:name>/', offer_views.get_all_offers, name='get_all_offers'),
    path('get_one_offer/<str:id>/', offer_views.get_one_offer, name='get_one_offer'),
    path('edit_offer_stock/<str:id>/', offer_views.edit_offer_stock, name='edit_offer_stock'),
    path('post_new_offer/<str:id>/', offer_views.post_new_offer, name='post_new_offer'),
] 