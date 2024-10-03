from django.urls import include, path

from .sets import set_offers_views

from .offers import bulk_edit_views, offer_views

from .orders import orders_views
from .returns import returns
from .photo_editor import photo_editor
from .pdf_creator import pdf_creator

from .messages import messages
from .views import *
from .messages import chatbot, messages
from .views_folder import accounts_views, orders_views_test, errors_views, generate_pdf, offers_listing
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

    path('get_orders/<str:name>/<str:delivery>/<str:status>/<str:client>/<str:fromDate>/<str:toDate>/', orders_views.get_orders, name='get_orders'),
    # path('get_orders_by_client/<str:name>/<str:delivery>/<str:status>/<str:client>/', orders_views_test.get_orders_by_client, name='get_orders_by_client'),
    path('get_order_details/<uuid:id>/<str:name>/', orders_views.get_order_details, name='get_order_details'),
    path('change_status/<str:id>/<str:name>/<str:status>/', orders_views.change_status, name='change_status'),
    path('run_option/<str:name>/<str:option>/', orders_views.run_option, name='run_option'),
    path('order_status/<str:name>/', orders_views.order_status, name='order_status'),

    # path('create_label_DPD/<uuid:id>/', orders_views_test.create_label_DPD, name='create_label_DPD'),
    # path('create_label_in_bulk_DPD/', orders_views_test.create_label_in_bulk_DPD, name='create_label_in_bulk_DPD'),

    # path('get_shipment_list/', orders_views.get_shipment_list, name='get_shipment_list'),
    path('set_shipment_list/<str:name>/', orders_views.set_shipment_list, name='set_shipment_list'), ###
    path('prepare_get_shipment_status_id/<str:name>/', orders_views.prepare_get_shipment_status_id, name='prepare_get_shipment_status_id'),
    # path('get_shipment_status_id/<str:name>/', orders.get_shipment_status_id, name='get_shipment_status_id'),

    path('invalid_token/<str:name>/', errors_views.invalid_token, name='invalid_token'),
    path('get_all_offers/<str:name>/', offer_views.get_all_offers, name='get_all_offers'),
    path('set_offers/<str:name>/', set_offers_views.set_offers, name='set_offers'),
    path('set_add/<str:name>/<str:offer_id>/', set_offers_views.set_add, name='set_add'),
    path('sets_add/<str:name>/<str:offer_id>/', set_offers_views.sets_add, name='sets_add'),
    path('add_offers/', set_offers_views.add_offers, name='add_offers'),
    path('add_offers_one/', set_offers_views.add_offers_one, name='add_offers_one'),
    path('add_discount/<str:name>/', set_offers_views.add_discount, name='add_discount'),
    path('add_copy_offers_one/', set_offers_views.add_copy_offers_one, name='add_copy_offers_one'),
    path('get_one_offer/<str:name>/<str:id>/', offer_views.get_one_offer, name='get_one_offer'),
    path('edit_offer_patch/<str:id>/', offer_views.edit_offer_patch, name='edit_offer_patch'),
    path('post_new_offer/<str:id>/', offer_views.post_new_offer, name='post_new_offer'),
    path('get_ean/', offer_views.get_ean, name='get_ean'),
    path('get_description/<str:id>/<str:name>/', offer_views.get_description, name='get_description'),
    # path('edit_offers_csv/<str:name>/', offer_views.edit_offers_csv, name='edit_offers_csv'),
    path('download_all_offers/<str:name>/', offer_views.download_all_offers, name='download_all_offers'),

    path('bulk_edit/<str:name>/<str:ed_value>/', bulk_edit_views.bulk_edit, name='bulk_edit'),
    path('PRICE/<str:name>/<str:secret>/<str:offers>/', bulk_edit_views.PRICE, name='PRICE'),
    path('QUANTITY/<str:name>/<str:secret>/<str:offers>/', bulk_edit_views.QUANTITY, name='QUANTITY'),
    path('DELIVERY_PRICE/<str:name>/<str:secret>/<str:offers>/', bulk_edit_views.DELIVERY_PRICE, name='DELIVERY_PRICE'),
    path('DELIVERY_TIME/<str:name>/<str:secret>/<str:offers>/', bulk_edit_views.DELIVERY_TIME, name='DELIVERY_TIME'),
    path('JSON_OFFERS/', bulk_edit_views.JSON_OFFERS, name='JSON_OFFERS'),
    path('upload_json_offers/<str:shipping_rates_id>/<str:after_sale_id>/<str:vat>/', offer_views.upload_json_offers, name='upload_json_offers'),

    path('all_messages/<str:name>/', messages.all_messages, name='all_messages'),
    path('get_one_message/', messages.get_one_message, name='get_one_message'),
    path('send_message/', messages.send_message, name='send_message'),
    # path('chatbot_response/', chatbot.chatbot_response, name='chatbot_response'),

    path('offers_listing/<str:name>/', offers_listing.offers_listing, name='offers_listing'),
    path('offers_listing_response/', offers_listing.offers_listing_response, name='offers_listing_response'),

    path('ebay_token/', ebay_token, name='ebay_token'),

    path('add_address/<str:name>/', add_address, name='add_address'),
    path('edit_address/<str:name>/', edit_address, name='edit_address'),
    path('get_address/<str:name>/', get_address, name='get_address'),

    path('get_invoice_file/<str:name>/<str:buyer>/', generate_pdf.get_invoice_file, name='get_invoice_file'),

    path('get_returns/<str:name>/', returns.get_returns, name='get_returns'),
    path('photo_editor/', photo_editor.remove_background, name='photo_editor'),
    path('remove_bg/', photo_editor.remove_bg, name='remove_bg'), 
    path('pdf_creator/', pdf_creator.pdf_creator, name='pdf_creator'),
] 