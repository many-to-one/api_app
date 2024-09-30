import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
import requests
import os
import base64
import time
import io
import zipfile
import PyPDF2
from django.conf import settings
from dotenv import load_dotenv

from ..api_service import async_service, sync_service

from ..celery_tasks.invoices_tasks import *
load_dotenv()
from ..models import *
from ..utils import *
from ..offers.offer_views import get_one_offer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import asyncio
import httpx


REDIRECT_URI = os.getenv('REDIRECT_URI')      # wprowadź redirect_uri
AUTH_URL = os.getenv('AUTH_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')



def get_orders(request, name, delivery, status, client, fromDate, toDate):

    if request.user.is_authenticated:

        # print('*********************** delivery **********************', delivery)
        # print('*********************** status **********************', status)
        # print('*********************** client **********************', client)
        # print('*********************** fromDate **********************', fromDate)
        # print('*********************** toDate **********************', toDate)

        all_results = []
        all_client_results = []
        result_with_name = []

        secret = Secret.objects.get(account__name=name)
        # print('*********************** NAME get_orders **********************', secret.account.name)
        debug_name = 'get_orders 34'
        url = 'order/checkout-forms' #"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms"
        orders = sync_service.Offers(name)
        result = orders.get_(request, url, debug_name)
        # print('*********************** ALL ORDERS **********************', result)
        result.update({'name': secret.account.name})
        all_results.append(result)
        # print('*********************** ALL ORDERS **********************', result["checkoutForms"][0])
        if client == 'all':
            all_client_results.append(result)
        else:
            # print('&&&&&&&&&&&&&&&&& I HERE $$$$$$$$$$$$$$$$$')
            for result in all_results:
                for res in result["checkoutForms"]:
                    if res["buyer"]["login"] == client:
                        all_client_results.append(res)

        
        if fromDate and toDate and status == 'all' and delivery == 'all' and client == 'all':
            for result in all_client_results:
                for res in result['checkoutForms']:
                    # print('***************** boughtAt ++ *******************', res['lineItems'][0]['boughtAt'][:10])
                    if res['lineItems'][0]['boughtAt'][:10] >= fromDate and res['lineItems'][0]['boughtAt'][:10] <= toDate:
                        # print('***************** boughtAt ++ *******************', res['lineItems'][0]['boughtAt'][:10])
                        result_with_name.append(res)

        if fromDate and toDate and status != 'all' and delivery == 'all' and client == 'all':
            for result in all_client_results:
                for res in result['checkoutForms']:
                    if res['lineItems'][0]['boughtAt'][:10] >= fromDate and res['lineItems'][0]['boughtAt'][:10] <= toDate and res["fulfillment"]["status"] == status:
                        result_with_name.append(res)

        if fromDate and toDate and status == 'all' and delivery != 'all' and client == 'all':
            for result in all_client_results:
                for res in result['checkoutForms']:
                    if res['lineItems'][0]['boughtAt'][:10] >= fromDate and res['lineItems'][0]['boughtAt'][:10] <= toDate and res['delivery']['method']["name"] == delivery:
                        result_with_name.append(res)

        if fromDate and toDate and status == 'all' and delivery == 'all' and client != 'all':
            for result in all_client_results:
                if result["buyer"]["login"] == client and result['lineItems'][0]['boughtAt'][:10] >= fromDate and result['lineItems'][0]['boughtAt'][:10] <= toDate:
                    result_with_name.append(result)

        if fromDate and toDate and status != 'all' and delivery == 'all' and client != 'all':
            for result in all_client_results:
                if result["buyer"]["login"] == client and result['lineItems'][0]['boughtAt'][:10] >= fromDate and result['lineItems'][0]['boughtAt'][:10] <= toDate and result["fulfillment"]["status"] == status:
                    result_with_name.append(result)

        if fromDate and toDate and status == 'all' and delivery != 'all' and client != 'all':
            for result in all_client_results:
                if result["buyer"]["login"] == client and result['lineItems'][0]['boughtAt'][:10] >= fromDate and result['lineItems'][0]['boughtAt'][:10] <= toDate and result['delivery']['method']["name"] == delivery:
                    result_with_name.append(result)

        if fromDate and toDate and status != 'all' and delivery != 'all' and client != 'all':
            for result in all_client_results:
                if result["buyer"]["login"] == client and result['lineItems'][0]['boughtAt'][:10] >= fromDate and result['lineItems'][0]['boughtAt'][:10] <= toDate and result['delivery']['method']["name"] == delivery and result["fulfillment"]["status"] == status:
                    result_with_name.append(result)
        
        if status == 'all': 
            for result in all_client_results:
                pass
                # print('***************** RESULTS FOR STATUS *******************', json.dumps(result, indent=4))
        if status == 'all' and delivery != 'all' and client == 'all' and fromDate == 'all' and toDate == 'all':
            # print('***************** status != all *******************')
            for result in all_client_results:
                # print('***************** RESULTS FOR STATUS *******************', json.dumps(result, indent=4))
                for res in result["checkoutForms"]:
                    # print('***************** RESULTS FOR STATUS *******************', json.dumps(res, indent=4))
                    if res['delivery']['method']["name"] == delivery:
                        result_with_name.append(res)
                # print('***************** RESULTS FOR STATUS *******************', json.dumps(result, indent=4))
        if status == 'all' and delivery != 'all' and client != 'all' and fromDate == 'all' and toDate == 'all':
            for result in all_client_results:
                if result["buyer"]["login"] == client and result["delivery"]["method"]["name"] == delivery:
                    # print('***************** RESULTS now*******************', json.dumps(result, indent=4))
                    result_with_name.append(result)


        if delivery == 'all' and status != 'all' and client == 'all' and fromDate == 'all' and toDate == 'all': 
            # print('***************** delivery == all *******************')
            for result in all_client_results:
                for res in result["checkoutForms"]:
                    if res['fulfillment']['status'] == status:
                        result_with_name.append(res)
        if status != 'all' and delivery == 'all' and client != 'all' and fromDate == 'all' and toDate == 'all':
            for result in all_client_results:
                # print('***************** RESULTS now*******************', result["fulfillment"]["status"])
                if result["buyer"]["login"] == client and result["fulfillment"]["status"] == status:
                    # print('***************** RESULTS now*******************', json.dumps(result, indent=4))
                    result_with_name.append(result)

        if delivery != 'all' and status != 'all' and client == 'all' and fromDate == 'all' and toDate == 'all':
            # print('YYYYYYYYYYYYYYYYEEEEEEEEEEEEEEEESSSSSSSSSSSSSSSSSSSSs')
            for result in all_client_results:
                # print('***************** RESULTS FOR STATUS *******************', json.dumps(result, indent=4))
                for res in result["checkoutForms"]:
                    # print('***************** RESULTS FOR STATUS *******************', json.dumps(res, indent=4))
                    if res['fulfillment']['status'] == status and res['delivery']['method']["name"] == delivery:
                        # print('***************** RESULTS FOR STATUS *******************', json.dumps(res, indent=4))
                        result_with_name.append(res)
        if delivery != 'all' and status != 'all' and client != 'all' and fromDate == 'all' and toDate == 'all':
            # print('@@@@@@@@@@@@@@ here @@@@@@@@@@@@@@@@@@')
            for result in all_client_results:
                # print('@@@@@@@@@@@@@@ here @@@@@@@@@@@@@@@@@@', json.dumps(result, indent=4))
                if result['fulfillment']['status'] == status and result['delivery']['method']["name"] == delivery and result["buyer"]["login"] == client:
                    # print('***************** RESULTS FOR STATUS *******************', status, delivery, client)
                    result_with_name.append(result)

        if delivery == 'all' and status == 'all' and client == 'all' and fromDate == 'all' and toDate == 'all':
            for result in all_client_results:
                # print('***************** COMMON *******************', json.dumps(result, indent=4))
                for res in result["checkoutForms"]:
                    # print('***************** ALL RESULTS LOOP *******************', json.dumps(res, indent=4))
                    result_with_name.append(res)

        if delivery == 'all' and status == 'all' and client != 'all' and fromDate == 'all' and toDate == 'all':
            for result in all_client_results:
                # print('***************** COMMON *******************', json.dumps(result, indent=4))
                result_with_name.append(result)


        # Paginate the results
        paginator = Paginator(result_with_name, 50)  # Show 10 results per page
        # print('***************** paginator.count *******************', paginator.count)
        # print('***************** paginator.num_pages *******************', paginator.num_pages)

        page_number = request.GET.get('page')
        try:
            paginated_results = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_results = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginated_results = paginator.page(paginator.num_pages)


        # all_delivery_methods = get_all_delivery_methods(request, secret, name)
        # print('*********************** all_delivery_methods **********************', all_delivery_methods)

        context = {
            'all_results': paginated_results, #sorted_results = sorted(all_results["checkoutForms"], key=lambda x: x["payment"]["finishedAt"])
            "name": name,
            # "deliveryMethods": all_delivery_methods,
        }
        # print('*********************** len all_results **********************', len(paginated_results))
        return render(request, 'orders/get_all_orders_test.html', context)
    

def get_order_details(request, id, name):
    
    url = f'order/checkout-forms/{id}'
    debug_name = 'get_order_details 202'
    order = sync_service.Offers(name)
    result = order.get_(request, url, debug_name)

    context = {
            'order': result,
        }
    
    return render(request, 'orders/get_order_details.html', context)
    

############ 1 ############

from ..views_folder.serializers import *
def set_shipment_list(request, name):

    # if request.user.is_authenticated:

        print('********************** name @@@ ****************************', name)

        start_time = time.time()

        ids = request.GET.getlist('ids')
        print('********************** IDS set_shipment_list IDS ****************************', ids)

        pickup = request.GET.getlist('pickup')
        secret = Secret.objects.get(account__name=name)
        try:
            address = Address.objects.get(name__name=name)
        except:
            return HttpResponse(f'Konto {name} nie posiada żadnego adresu wysyłki.')
        secret_data = SecretSerializer(secret).data
        address_data = AddressSerializer(address).data
        # time.sleep(2)
        print('********************** secret @@@ ****************************', secret)
        print('********************** address @@@ ****************************', address)
        
        if address:
            results = asyncio.run(set_shipment_list_async(request, ids, secret, address_data))#[0]
        print('********************** /// results 904/// ****************************', results)  #results[1][1]
        # time.sleep(1)
        if results:
            if secret:
                results_ = asyncio.run(set_shipment_list_q(results, secret))
                products = asyncio.run(get_products(results, secret))
                print('**********************  /// results_ 909 /// ****************************', results_)

                # get_invoice_task.apply_async(args=['8'])
                # invoice = asyncio.run(get_invoice(request, results, secret_data, name, address_data) )
                # invoice_task_res = invoice_task.delay('5')
                # print('********************** get_invoice ****************************', invoice)

        keywords = {
            'DHL': [
                '11:30 13:30',
                '13:30 15:30',
                '15:30 17:30',
            ], 
            'UPS': [
                "09:00 12:00",
                "10:00 12:00",
                "11:00 13:00",
                "12:00 14:00",
                "14:00 16:00",
            ], 
            'DPD': [
                '09:00 12:00',
                '13:00 16:00',
            ], 
            'ORLEN': [
                '13:00 15:00',
            ], 
            'Pocztex': [
                '08:00 15:00',
            ],
        }
        selects = set()
        couriers = []
        for res in results_:
            print('********************** referenceNumber ****************************', res["input"]["referenceNumber"])
            for courier, times in keywords.items():
                if courier in res["input"]["referenceNumber"]:
                    selects.add((courier, tuple(times)))
            couriers.append(res["input"]["referenceNumber"])
        
        print(' ********************** SELECTS ********************** ', selects)

        context = {
            'result': results_,
            'name': name,
            'couriers': couriers,
            'selects': selects,
            'warehouse_list': products,
            }
        
        # print('********************** context 921 ****************************', context)
        print('********************** warehouse_list ****************************', products)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"********************** set_shipment_list finished time: {elapsed_time} seconds **********************")

        return render(request, 'orders/set_pickup.html', context)



############ 2 ############
async def set_shipment_list_async(request, ids, secret, address):

    # if request.user.is_authenticated:

        tasks = []
        # secret = await sync_to_async(Secret.objects.get)(account__name=name)
        for item in ids:
            for order_data in item.split('@'):
                if order_data:
                    order = order_data.split(":")
                    if order[0].startswith(','):
                        id = order[0][1:]
                    else:
                        id = order[0] 
                    name = order[1]
                    deliveryMethod = order[2]
                    offerId = order[3]
                    print('(((((((((((((((((((order_data:))))))))))))))))))', id, name, deliveryMethod, offerId)
    
                    tasks.append(asyncio.create_task(get_shipment_id(request, secret, name, deliveryMethod)))
                    tasks.append(asyncio.create_task(
                        combined_task(request, id, name, offerId, secret, address)
                        ))
                    # tasks.append(asyncio.create_task(get_offer_descr(request, offerId, secret)))

        results = await asyncio.gather(*tasks)
        print('(((((((((((((((((((results:))))))))))))))))))', results)

        return results  


############ 3 ############
async def get_shipment_id(request, secret, name, deliveryMethod):

    """ credentialsId i packageTypes przewoźnika """

    url = 'shipment-management/delivery-services' #f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/delivery-services"
    token = secret.access_token
    refresh_token = secret.refresh_token
    name = secret.account.name
    debug_name = 'get_shipment_id 306'
     
    result = await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)
    for r in result['services']:
        # print('************ LOOP ID ************', r['id'])
        # print('************ LOOP NAME ************', r['name'])
        if r['name'] == deliveryMethod and r['marketplaces'] == ['allegro-pl']:
            print('************ $$$ get_shipment_id packageTypes 322 $$$ ************', r)
            print('************ get_shipment_id ************', r['name'], '----', r['id']['deliveryMethodId'], '----', r['marketplaces'])
            # if r['id']['credentialsId']:
            #     print('************ r[id][credentialsId] ************', r['id']['credentialsId'])
            #     res = {
            #         "credentialsId": r['id']['credentialsId'],
            #         "packageTypes": r['packageTypes'][0]
            #     }
            #     return res #r['id']['credentialsId']
            # else:
            #     return None
            res = {
                    "credentialsId": r['id']['credentialsId'],
                    "packageTypes": r['packageTypes'][0]
                }
            return res
        

############ 4 ############
async def combined_task(request, id, name, offerId, secret, address):

    label, offer_descr = await asyncio.gather(
        create_label(request, id, name, secret),
        get_offer_descr(request, offerId, secret),
    )
    print('************ combined_task ************', label, offer_descr, address)
    return label, offer_descr, address
    

############ 5 ############
async def create_label(request, id, name, secret):

    url = f'order/checkout-forms/{id}' #f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{id}"
    token = secret.access_token
    refresh_token = secret.refresh_token
    name = secret.account.name
    debug_name = 'create_label 329'

    return await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)
        


############ 6 ############
async def get_offer_descr(request, id, secret):

    url = f'sale/product-offers/{id}' #f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
    token = secret.access_token
    refresh_token = secret.refresh_token
    name = secret.account.name
    debug_name = 'get_offer_descr 341'

    result = await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)
    item_height = ""
    item_width = ""
    item_length = ""
    item_wieght = ""
    for item in result["productSet"][0]["product"]["parameters"]:
        if item["id"] == "223329":
            item_height = item["values"][0]
            # print('************** get_one_offer item **************', item["values"][0])
        if item["id"] == "223333":
            item_width = item["values"][0]
        if item["id"] == "201321":
            item_length = item["values"][0]
        if item["id"] == "17448":
            item_wieght = item["values"][0]

    return [item_length, item_width, item_height, item_wieght]



############ 7 ############
async def set_shipment_list_q(results, secret):

    print('********************** set_shipment_list_q results ****************************', results[0]['packageTypes'])
    print('********************** set_shipment_list_q secret ****************************', secret)
        # print('********************** results[0] ****************************', results[0])
        # print('********************** results[1] ****************************', results[1])

    tasks = []
    externalId = set()
    packageTypes = results[0]['packageTypes']

    if results:
        for order_data in results[1:]:
            if isinstance(order_data, tuple):
                for _ in range(int(order_data[0]["delivery"]["calculatedNumberOfPackages"])):
                    for line_item in order_data[0]['lineItems']:
                        externalId.add(f"{line_item['offer']['external']['id']} x {line_item['quantity']}")
                    external_id = ', '.join(sorted(externalId))
                    # print('********************** external_id ****************************', external_id)
                    # print('********************** order_data all ****************************', order_data)
                    descr_ = order_data[1]
                    user_ = order_data[2]
                    print('********************** order_data here [descr_ , user_] ****************************', descr_ ,user_)
                    # print('********************** order_data here [lineItems] ****************************', len(order_data[0]['lineItems']))
                    # if len(order_data[0]['lineItems']) > 1:

                    #     for data in order_data:
                    #         # print('********************** order_data here [data] ****************************', data)
                    #         # print('********************** order_data here [data] ****************************', order_data[0]['lineItems'])
                    #         tasks.append(asyncio.create_task(
                    #             test(
                    #                 secret, 
                    #                 data,
                    #                 external_id,
                    #                 external_id,  
                    #                 descr_,
                    #                 user_,
                    #             )
                    #         ))

                    tasks.append(asyncio.create_task(
                        test(
                            secret, 
                            order_data[0],
                            external_id,
                            external_id,  
                            order_data[1],
                            order_data[2],
                            packageTypes,
                        )
                    ))
                    externalId = set()

    return await asyncio.gather(*tasks)


async def get_products(results, secret):
    lists = []
    for order_data in results[1:]:
        if isinstance(order_data, tuple):
            for _ in range(int(order_data[0]["delivery"]["calculatedNumberOfPackages"])):
                for line_item in order_data[0]['lineItems']:
                    print( '********************** get_products **********************', line_item['offer'] )
                    lists.append(line_item)

    print( '********************** BASE 64 GET PRODUCTS lists **********************', lists )

    # res = await warehouse_list_pdf(lists)
    # return res
    return lists



from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse
import json

async def warehouse_list_pdf(lists):
    # Convert the list data to JSON string format
    json_str = json.dumps(lists, indent=4)

    # Create a BytesIO buffer
    buffer = BytesIO()

    # Create the PDF in the buffer instead of saving it to the file system
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add content to the PDF
    c.drawString(100, height - 100, "Warehouse List Data:")
    text_object = c.beginText(100, height - 120)
    text_object.textLines(json_str)
    c.drawText(text_object)

    # Finalize and save the PDF content into the buffer
    c.save()

    # Get the buffer value and prepare the response
    buffer.seek(0)  # Rewind the buffer to the beginning
    response = HttpResponse(buffer, content_type='application/pdf')

    # Optionally, set a filename for the downloaded PDF
    response['Content-Disposition'] = 'attachment; filename="warehouse_lists.pdf"'

    # Close the buffer
    buffer.close()

    return response






############ 8 ############
def prepare_get_shipment_status_id(request, name):

    secret = Secret.objects.get(account__name=name)
    print('********************** prepare_get_shipment_status_id ****************************', secret)

    # ids = request.GET.getlist('ids')
    ids_json = request.GET.get('ids')
    ids = json.loads(ids_json)
    pickup = request.GET.getlist('pickup')
    print('@@@@@@@@@ ids @@@@@@@@@', ids)
    print('@@@@@@@@@ pickup @@@@@@@@@', pickup)

    return asyncio.run(get_shipment_status_id(request, name, secret, ids, pickup))



############ 9 ############
async def get_shipment_status_id(request, name, secret, ids, pickup):

    # if request.user.is_authenticated:

    start_time = time.time()
    tasks = []
    labels = []

    # print('********************** TIME TIME TIME 0 SECONDS secret ****************************', secret)
    # await asyncio.sleep(2)
    courier = None
    for item in ids:
        if item.get('courier'):  # Safely check if 'courier' exists
            courier = item.get('courier')
            print('@@@@@@@@@ ITEM COURIER @@@@@@@@@', item.get('courier'))
        else:
            print('@@@@@@@@@ ITEM @@@@@@@@@', item)

    for item in ids:
        tasks.append(asyncio.create_task(
            label_print(
                request, 
                await make_order(request, secret, item['commandId'], courier, pickup), 
                secret
                )
            ))


    labels = await asyncio.gather(*tasks)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"********************** FINISH time: {elapsed_time} seconds **********************")
    labelsPrint = await base64_to_pdf_bulk(labels)
    if labelsPrint is None:
        return JsonResponse({'message': 'No valid labels found'})
    return labelsPrint



############ 10 ############
async def label_print(request, shipmentId, secret):

    url = 'shipment-management/label' #f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/label" 
    payload = {
                "shipmentIds": [
                shipmentId
                ],
                "pageSize": "A6",
            }
    token = secret.access_token
    refresh_token = secret.refresh_token
    name = secret.account.name
    debug_name = 'label_print 469'
    
    if shipmentId is not None:
        response = await async_service.async_post(request, url=url, payload=payload, token=token, refresh_token=refresh_token, name=name, debug_name=debug_name)
        if response.status_code == 404:
            # print(f"********************** label_prints **********************", shipmentId)
            return await create_pdf_bytes(shipmentId)
        else:
            # print(f"********************** label_prints response.content **********************", shipmentId)
            return response.content
    else:
        return None
    

from reportlab.lib.pagesizes import A6
async def create_pdf_bytes(text):
    # Create a BytesIO buffer to hold the PDF data
    buffer = BytesIO()
    
    # Create a PDF canvas with A6 page size
    pdf = canvas.Canvas(buffer, pagesize=A6)
    
    # Set the font and size
    pdf.setFont("Helvetica", 10)
    
    # Insert the text into the PDF
    pdf.drawString(10, 400, text)  # Adjusting coordinates to fit A6 size
    
    # Finalize the PDF
    pdf.showPage()
    pdf.save()

    # Get the PDF data from the buffer
    pdf_data = buffer.getvalue()
    
    # Close the buffer
    buffer.close()

    return pdf_data
        


############ 11 ############
pickup_tasks = []
async def make_order(request, secret, commandId, courier, pickup):

    url = f'shipment-management/shipments/create-commands/{commandId}' #f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/shipments/create-commands/{commandId}"
    token = secret.access_token
    refresh_token = secret.refresh_token
    name = secret.account.name
    debug_name = 'label_print 469'

    print('@@@@@@@@@ MAKE ORDER commandId @@@@@@@@@', commandId)
    # print('@@@@@@@@@ MAKE ORDER courier @@@@@@@@@', courier)
    # time.sleep(2)
    while True:
        result = await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)
        print('@@@@@@@@@ MAKE ORDER result @@@@@@@@@', result)
        if result["shipmentId"] is not None:
            print('@@@@@@@@@ MAKE ORDER result["shipmentId"] @@@@@@@@@', result["shipmentId"])
            # if pickup[0] == 'pickup':
            if courier is not None:
                asyncio.create_task(async_proposals_and_courier(request, result["shipmentId"], secret, commandId, courier))
            return result["shipmentId"]
        if result['status'] == 'ERROR':
            print('@@@@@@@@@ MAKE ORDER ERROR @@@@@@@@@', result['errors'][0]['userMessage'])
            return result['errors'][0]['userMessage']
            # break

        

############ 12 ############
async def base64_to_pdf_bulk(base64_data_list):

    pdf_writer = PyPDF2.PdfWriter()

    try:
        for base64_data in base64_data_list:
            # print(' @@@@@@@@@@@@@@@@@ INSIDE base64_data @@@@@@@@@@@@@@@@@ ', base64_data)
            # Decode the Base64 data
            if base64_data is not None:
                binary_data = base64_data #base64.b64decode(base64_data)
                # print(' @@@@@@@@@@@@@@@@@ INSIDE binary_data @@@@@@@@@@@@@@@@@ ', binary_data)

                # Create a PdfReader object
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(binary_data))
                # print(' @@@@@@@@@@@@@@@@@ INSIDE pdf_reader @@@@@@@@@@@@@@@@@ ', pdf_reader)

                # Merge each page from the PdfReader object into the PdfWriter object
                for page_num in range(len(pdf_reader.pages)):
                    pdf_writer.add_page(pdf_reader.pages[page_num])
            else:
                None

        # Create a BytesIO buffer to write the merged PDF
        output_buffer = io.BytesIO()
        print(' @@@@@@@@@@@@@@@@@ INSIDE output_buffer @@@@@@@@@@@@@@@@@ ') #output_buffer
        pdf_writer.write(output_buffer)

        # Set the appropriate content type for PDF
        response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')

        # Optionally, set a filename for the downloaded PDF
        response['Content-Disposition'] = 'attachment; filename="merged_labels.pdf"'
        return response
    except Exception as e:
        print("Error:", e)


############ 13 ############
async def async_proposals_and_courier(request, shipmentId, secret, commandId, courier):

    """ Zamówić Kuriera z datą i godziną odbioru """

    # Zyskujemy proponowane daty odbioru przez przewoźnika
    pickupDateProposalId = await get_pickup_proposals(request, secret, shipmentId, courier)
    if pickupDateProposalId:
        # po wybraniu daty i godziny odbioru zamawiamy kuriera
        await get_courier(request, shipmentId, commandId, pickupDateProposalId, secret)



############ 14 ############
async def get_pickup_proposals(request, secret, shipmentId, courier):

    """ Proponowana data odbioru paczek przez kuriera """

    print(' ^^^^^^^^^^^^^^^^^ courier["date"] ^^^^^^^^^^^^^^^^^ 662 ', courier["date"][11:])

    url = 'shipment-management/pickup-proposals' #f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/pickup-proposals" 
    payload = {
                "shipmentIds": [
                    shipmentId
                ],
                  "readyDate": courier["date"][:10]#"2024-09-10" #ship_time
            }
    token = secret.access_token
    refresh_token = secret.refresh_token
    name = secret.account.name
    debug_name = 'get_pickup_proposals 647'

    response = await async_service.async_post(request, url=url, payload=payload, token=token, refresh_token=refresh_token, name=name, debug_name=debug_name)
    result = response.json()
    print(' ^^^^^^^^^^^^^^^^^ GET PICKUP PROPOSAILS RESULT ALL 678 ^^^^^^^^^^^^^^^^^ ', result)
    for res in result[0]["proposals"][0]["proposalItems"]:
        print(' ^^^^^^^^^^^^^^^^^ GET PICKUP PROPOSAILS 679 ^^^^^^^^^^^^^^^^^ ', res)
        if courier["date"] == res["name"]:
            print(' ^^^^^^^^^^^^^^^^^ courier["date"] == res["name"] ^^^^^^^^^^^^^^^^^ ', res, res["id"])
            return  res["id"]
        elif courier["date"][11:] == res["name"][11:]:
            print(' ^^^^^^^^^^^^^^^^^ courier["date"][12:] == res["name"][12:] ^^^^^^^^^^^^^^^^^ ', res, res["id"])
            return  res["id"] #result[0]["proposals"][0]["proposalItems"][0]["id"]
        else:
            print(' ^^^^^^^^^^^^^^^^^ CHECKED PICKUP PROPOSAILS ANY 683 ^^^^^^^^^^^^^^^^^ ', res, courier)
            return  "ANY" #for Inpost



############ 15 ############
async def get_courier(request, shipmentId, commandId, pickupDateProposalId, secret):

    url = 'shipment-management/pickups/create-commands' #"https://api.allegro.pl.allegrosandbox.pl/shipment-management/pickups/create-commands"  
    payload = {
                "commandId": commandId,
                "input": {
                    "shipmentIds": [
                    shipmentId
                    ],
                    "pickupDateProposalId": pickupDateProposalId
                }
            }
    token = secret.access_token
    refresh_token = secret.refresh_token
    name = secret.account.name
    debug_name = 'get_courier 587'

    await async_service.async_post(request, url=url, payload=payload, token=token, refresh_token=refresh_token, name=name, debug_name=debug_name)
    # return HttpResponse('ok')



######################################### CHANGE ORDER STATUS ##############################################

def run_option(request, name, option):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)
        ids = request.GET.getlist('ids')

        result = asyncio.run(run_option_async(secret, option, ids))

        print('*********** run_option main ***********', result)

        individual_ids = []

        # Iterate over each element in the 'ids' list
        for id_group in ids:
            # Split each string by commas and extend the individual_ids list with the resulting elements
            individual_ids.extend(id_group.split(','))

        return JsonResponse(
                    {
                        'message': 'Stock updated successfully',
                        'newStatus': option,
                        'orders': individual_ids,
                    }, 
                    status=200,
                )


async def run_option_async(secret, option, ids):

    tasks = []

    for item in ids:
        for order_id in item.split(','):
            if order_id:
                print('********************** run_option order_id ****************************', order_id)
                tasks.append(asyncio.create_task(change_status_async(secret, option, order_id)))

    results = await asyncio.gather(*tasks)

    return results


async def change_status_async(secret, option, order_id):

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{order_id}/fulfillment"
        headers = {
        'Authorization': f'Bearer {secret.access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }

        data = {
                "status": str(option),
                "shipmentSummary": {
                "lineItemsSent": "SOME"
                }
            }

        response = requests.put(url, headers=headers, json=data)
        print('*********** change_status ***********', response)

        return response
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    


def change_status(request, id, name, status):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)
        # ids = request.GET.getlist('ids')
        # encoded_offers = ','.join(ids)
        # print('********************** change_status ids ****************************', ids)

        try:
            url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{id}/fulfillment"
            headers = {
            'Authorization': f'Bearer {secret.access_token}',
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Content-Type': 'application/vnd.allegro.public.v1+json'
        }

            data = {
                    "status": str(status),
                    "shipmentSummary": {
                    "lineItemsSent": "SOME"
                    }
                }

            response = requests.put(url, headers=headers, json=data)
            print('*********** change_status ***********', id, name, status)
            print('*********** change_status ***********', response)

            return JsonResponse(
                    {
                        'message': 'Stock updated successfully',
                        'newStatus': status,
                    }, 
                    status=200,
                )
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        

def order_status(request, name):
    return render(request, 'orders/order_status.html', {'name': name})