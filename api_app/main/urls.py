from django.urls import include, path
from .views import *
from .views_folder import accounts_views, orders_views_test, orders_views, errors_views, offer_views, messages, generate_pdf, bulk_edit_views
from .ebay.views import *

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

    path('get_orders/<str:name>/<str:delivery>/<str:status>/<str:client>/', orders_views_test.get_orders, name='get_orders'),
    path('get_orders_by_client/<str:name>/<str:delivery>/<str:status>/<str:client>/', orders_views_test.get_orders_by_client, name='get_orders_by_client'),
    path('get_order_details/<uuid:id>/<str:name>/', orders_views_test.get_order_details, name='get_order_details'),
    path('change_status/<uuid:id>/<str:name>/<str:status>/<str:delivery>/', orders_views.change_status, name='change_status'),
    # path('create_label_DPD/<uuid:id>/', orders_views_test.create_label_DPD, name='create_label_DPD'),
    # path('create_label_in_bulk_DPD/', orders_views_test.create_label_in_bulk_DPD, name='create_label_in_bulk_DPD'),

    path('get_shipment_list/', orders_views_test.get_shipment_list, name='get_shipment_list'),
    path('set_shipment_list/<str:name>/', orders_views_test.set_shipment_list, name='set_shipment_list'), ###
    path('get_shipment_status_id/<str:name>/', orders_views_test.get_shipment_status_id, name='get_shipment_status_id'),

    path('invalid_token', errors_views.invalid_token, name='invalid_token'),
    path('get_all_offers/<str:name>/', offer_views.get_all_offers, name='get_all_offers'),
    path('get_one_offer/<str:id>/', offer_views.get_one_offer, name='get_one_offer'),
    path('edit_offer_stock/<str:id>/', offer_views.edit_offer_stock, name='edit_offer_stock'),
    path('post_new_offer/<str:id>/', offer_views.post_new_offer, name='post_new_offer'),
    path('get_ean/', offer_views.get_ean, name='get_ean'),
    path('get_description/<str:id>/<str:lister>/', offer_views.get_description, name='get_description'),
    path('edit_offers_csv/<str:name>/', offer_views.edit_offers_csv, name='edit_offers_csv'),
    path('bulk_edit/<str:name>/<str:ed_value>/', bulk_edit_views.bulk_edit, name='bulk_edit'),
    path('PRICE/<str:name>/<str:offers>/', bulk_edit_views.PRICE, name='PRICE'),

    path('all_messages/<str:name>/', messages.all_messages, name='all_messages'),
    path('get_one_message/', messages.get_one_message, name='get_one_message'),
    path('send_message/', messages.send_message, name='send_message'),

    path('ebay_token/', ebay_token, name='ebay_token'),

    path('add_address/<str:name>/', add_address, name='add_address'),
    path('get_address/<str:name>/', get_address, name='get_address'),

    path('get_invoice_file/<str:name>/<str:buyer>/', generate_pdf.get_invoice_file, name='get_invoice_file'),
] 