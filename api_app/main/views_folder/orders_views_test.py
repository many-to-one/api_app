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
from dotenv import load_dotenv

from ..celery_tasks.orders_tasks import my_task, my_new_task
load_dotenv()
from ..models import *
from ..utils import *
from .offer_views import get_one_offer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import asyncio
import httpx
from asgiref.sync import sync_to_async

REDIRECT_URI = os.getenv('REDIRECT_URI')      # wprowadź redirect_uri
AUTH_URL = os.getenv('AUTH_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')


# def get_accounts(request):
#     accounts = Allegro.objects.filter(user=request.user).all()
#     context = {
#         'accounts': accounts,
#     }

#     return render(request, 'get_accounts.html', context)


def get_orders(request, name, delivery):

    print('*********************** delivery **********************', delivery)

    all_results = []
    result_with_name = []

    secret = Secret.objects.get(account__name=name)
    # print('*********************** NAME get_orders **********************', secret.account.name)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms"
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        # print('***********************secret.access_token**********************', secret.access_token)
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        result.update({'name': secret.account.name})
        all_results.append(result)
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token, name)
                    # Retry fetching orders with the new token
                    return get_orders(request)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    context = {'name': name}
                    return render(request, 'invalid_token.html', context)
        # print('*********************** ALL ORDERS IN **********************', json.dumps(result, indent=4))
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    if delivery == 'all': 
        for result in all_results:
            for res in result["checkoutForms"]:
                result_with_name.append(res)
                # print('***************** RESULTS FOR PAGINATION *******************', json.dumps(res, indent=4))
        #         if res["fulfillment"]["status"] == 'NEW':
        #             print('***************** ALL RESULTS LOOP *******************', "NEW-tak")

    else:
        for result in all_results:
            for res in result["checkoutForms"]:
                # print('***************** delivery method *******************', res['id'])
                if res['delivery']['method']["name"] == delivery:
                    result_with_name.append(res)


    # Paginate the results
    paginator = Paginator(result_with_name, 50)  # Show 10 results per page
    print('***************** paginator.count *******************', paginator.count)
    print('***************** paginator.num_pages *******************', paginator.num_pages)

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
    return render(request, 'get_all_orders_test.html', context)
    

def get_order_details(request, id, name):

    # accounts = Allegro.objects.filter(user=request.user)
    # for account in accounts:
    secret = Secret.objects.get(account__name=name)

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{id}"
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token, name)
                    # Retry fetching orders with the new token
                    return get_order_details(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    context = {'name': name}
                    return render(request, 'invalid_token.html', context)

        print('@@@@@@@@@ GET ORDER DETAILS @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'order': product_result.json()
        }
        return render(request, 'get_order_details.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
        



#################################################################################################################################
############################################# CREATE A MANY DPD LABELS LOGIC ####################################################
#################################################################################################################################

def create_label_in_bulk(request, result):
    """
        This function returns the description of each order in orders array,
        such as delivery and product information to use it in DPD label.
    """

    # print('********************** CREATE LABEL IN BULK CALLED ****************************', ids_arr)
    all_results = []

    # accounts = Allegro.objects.filter(user=request.user)
    # for account in accounts:
    #     secret = Secret.objects.get(account=account)

    for order in result:
        secret = Secret.objects.get(account__name=order['name'])
        # print('**************************** SECRET ****************************', secret.access_token)
        try:
            # print('**************************** RESULT FOR ID ****************************', id)
            url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{order['id']}"
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            product_result = requests.get(url, headers=headers, verify=True)
            result = product_result.json()  
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, secret.account.name)
                        # Retry fetching orders with the new token
                        return get_order_details(request, id)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': secret.account.name}
                        return render(request, 'invalid_token.html', context)
            # print('RESULT FOR DPD @@@@@@@@@*****', json.dumps(result, indent=4))
            # print('RESULT status @@@@@@@@@*****', product_result.status_code)
            if product_result.status_code == 200:
                all_results.append({'result': result, 'name': secret.account.name})
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
            
    return all_results
        


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



#################################################################################################################################
############################################## CREATE A ONE DPD LABEL LOGIC #####################################################
#################################################################################################################################

async def create_label(request, id, name, secret):

    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{id}"
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            product_result = await client.get(url, headers=headers) #verify=True
            result = product_result.json()
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, name)
                        # Retry fetching orders with the new token
                        return create_label(request, id, name)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': name}
                        return render(request, 'invalid_token.html', context)
            print('@@@@@@@@@ PUNKT ODBIORU ID @@@@@@@@@', json.dumps(result, indent=4))
            print('@@@@@@@@@ CRETAE LABEL HEADERS @@@@@@@@@', product_result.headers)

            return result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)




def change_status(request, id, name, status, delivery):

    secret = Secret.objects.get(account__name=name)

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
        # print('*********** change_status ***********', response)

        return JsonResponse(
                {
                    'message': 'Stock updated successfully',
                    'newStatus': status,
                }, 
                status=200,
            )
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    


# def get_all_delivery_methods(request, secret, name):

#     results = []
#     try:
#         url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/delivery-services"
#         headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
#         product_result = requests.get(url, headers=headers) #verify=True
#         result = product_result.json()
#         if 'error' in result:
#             error_code = result['error']
#             if error_code == 'invalid_token':
#                 # print('ERROR RESULT @@@@@@@@@', error_code)
#                 try:
#                     # Refresh the token
#                     new_token = get_next_token(request, secret.refresh_token, name)
#                     # Retry fetching orders with the new token
#                     return get_order_details(request, id)
#                 except Exception as e:
#                     print('Exception @@@@@@@@@', e)
#                     context = {'name': name}
#                     return render(request, 'invalid_token.html', context)
#         for r in result['services']:
#             print('************ LOOP ID ************', r['id'])
#             print('************ LOOP NAME ************', r['name'])
#             results.append(r['name'])
            
#         return results

#     except requests.exceptions.HTTPError as err:
#         raise SystemExit(err)

    

async def get_shipment_id(request, secret, name, deliveryMethod):

    # time.sleep(1)

    """ Umowa własna z przewoźnikiem """
     
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/delivery-services"
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            product_result = await client.get(url, headers=headers) #verify=True
            result = product_result.json()
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, name)
                        # Retry fetching orders with the new token
                        return get_order_details(request, id)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': name}
                        return render(request, 'invalid_token.html', context)
            for r in result['services']:
                # print('************ LOOP ID ************', r['id'])
                # print('************ LOOP NAME ************', r['name'])
                if r['name'] == deliveryMethod and r['marketplaces'] == ['allegro-pl']:
                    # print('************ Allegro Kurier DPD ID ************', r['name'], '----', r['id']['deliveryMethodId'], '----', r['marketplaces'])
                    if r['id']['credentialsId']:
                        return r['id']['credentialsId']
                    else:
                        return None
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    # return HttpResponse('ok')


async def get_offer_descr(request, id, secret):

    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
            # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            product_result = await client.get(url, headers=headers) #verify=True
            result = product_result.json()
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token)
                        # Retry fetching orders with the new token
                        return get_one_offer(request, id)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        return redirect('invalid_token')
            # print('RESULT - get_one_offer - @@@@@@@@@', json.dumps(result, indent=4))
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

        
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

async def combined_task(request, id, name, offerId, secret):
    return await create_label(request, id, name, secret), await get_offer_descr(request, offerId, secret), await get_user(secret)


async def set_shipment_list_async(request, ids, secret):

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
                print('order_data:', id, name, deliveryMethod, offerId)
 
                tasks.append(asyncio.create_task(get_shipment_id(request, secret, name, deliveryMethod)))
                tasks.append(asyncio.create_task(
                    combined_task(request, id, name, offerId, secret)
                    ))
                # tasks.append(asyncio.create_task(get_offer_descr(request, offerId, secret)))

    results = await asyncio.gather(*tasks)

    return results   


# @sync_to_async
def get_secret(name):
    # secret = await sync_to_async(Secret.objects.get)(account__name=name)
    secret = Secret.objects.get(account__name=name)
    return secret


async def set_shipment_list_q(results, secret):
    # start_time = time.time()

    # print('********************** set_shipment_list_q results ****************************', results)
    print('********************** set_shipment_list_q secret ****************************', secret)
    # print('********************** results[0] ****************************', results[0])
    # print('********************** results[1] ****************************', results[1])

    from ..utils import pickup_point_order, no_pickup_point_order, cash_no_point_order, test

    tasks = []

    if results:
        
            [
                tasks.append(asyncio.create_task(
                test(
                    secret, 
                    order_data[0],
                    order_data[0]['lineItems'][0]['offer']['external']['id'],
                    order_data[0]['lineItems'][0]['offer']["name"][:15],
                    order_data[1],
                    order_data[2],
                )
                ))
                for order_data in results
                if isinstance(order_data, tuple)
            ]
    

    # return HttpResponse('ok')
    return await asyncio.gather(*tasks)


async def get_user(secret):
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://api.allegro.pl.allegrosandbox.pl/me" 
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 

            response = await client.get(url, headers=headers)
            result = response.json()

            # print('@@@@@@@@@ RESULT GET USER @@@@@@@@@', json.dumps(result, indent=4))
            # print('@@@@@@@@@ RESPONSE GET USER HEADERS @@@@@@@@@', response.headers)
            # change_status(request, id, secret.account.name, 'SENT')
            # time.sleep(7)
            return  result
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)


# @sync_to_async
def set_shipment_list(request, name):

    start_time = time.time()

    ids = request.GET.getlist('ids')
    print('********************** IDS set_shipment_list IDS ****************************', ids)

    pickup = request.GET.getlist('pickup')
    secret = Secret.objects.get(account__name=name)
    # time.sleep(2)
    print('********************** secret @@@ ****************************', secret)
    results = asyncio.run(set_shipment_list_async(request, ids, secret))#[0]
    # print('********************** /// results /// ****************************', results)  #results[1][1]
    # time.sleep(1)
    if results:
        if secret:
            results_ = asyncio.run(set_shipment_list_q(results, secret))
            # print('**********************  /// results_secret /// ****************************', secret)

    context = {
        'result': results_,
        'name': name,
        }
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"********************** set_shipment_list finished time: {elapsed_time} seconds **********************")

    return render(request, 'set_pickup.html', context)

    # return HttpResponse('ok')

pickup_tasks = []
async def make_order(request, secret, commandId, pickup):

    # print('@@@@@@@@@ MAKE ORDER commandId @@@@@@@@@', commandId)
    # pickup_tasks = []

    while True:
        async with httpx.AsyncClient() as client:
            url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/shipments/create-commands/{commandId}"
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"} 

            response = await client.get(url, headers=headers)
            result = response.json()

            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, 'retset')
                        # Retry fetching orders with the new token
                        return get_order_details(request, id)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': 'retset'}
                        return render(request, 'invalid_token.html', context)
                    
            if result["status"] == "ERROR":
                # print('@@@@@@@@@ MAKE ORDER VALIDATION_ERROR @@@@@@@@@', json.dumps(result, indent=4))
                result["shipmentId"] == None
                return result["shipmentId"]

        # print('@@@@@@@@@ MAKE ORDER RESULT @@@@@@@@@', json.dumps(result, indent=4))
        print('@@@@@@@@@ MAKE ORDER HEADERS @@@@@@@@@', response.headers)
        # print('@@@@@@@@@ MAKE ORDER VALIDATION_ERROR @@@@@@@@@', result['errors'][0]["code"])
    
        if result["shipmentId"] is not None:
            # print('@@@@@@@@@ MAKE ORDER result["shipmentId"] @@@@@@@@@', result["shipmentId"])
            if pickup[0] == 'pickup':
                asyncio.create_task(async_proposals_and_courier(request, result["shipmentId"], secret.access_token, commandId))
            return result["shipmentId"]




async def get_shipment_status_id(request, name):

    start_time = time.time()
    tasks = []
    # pickup_tasks = []
    courier_tasks = []
    # while True:
    labels = []
    ids = request.GET.getlist('ids')
    pickup = request.GET.getlist('pickup')
    print('@@@@@@@@@ ids @@@@@@@@@', ids)
    print('@@@@@@@@@ pickup @@@@@@@@@', pickup)

    secret = await sync_to_async(Secret.objects.get)(account__name=name)
        # print('********************** TIME TIME TIME 0 SECONDS ****************************')

        # time.sleep(5)

    parts_list = [
        part.split(':')
        for item in ids
        for part in item.split(',')
    ]

    order_tasks = [
        tasks.append(asyncio.create_task(
            label_print(
                request, 
                await make_order(request, secret, commandId, pickup), 
                secret
                )
            ))
        for commandId, name in parts_list
    ]

    labels = await asyncio.gather(*tasks)
        # return labels

    # if any(label is not None for label in labels):
    #     print('@@@@@@@@@@@@@@@@@@ LABELS @@@@@@@@@@@@@@@@@@@@') #labels
    #     end_time = time.time()
    #     elapsed_time = end_time - start_time
    #     print(f"********************** FINISH time: {elapsed_time} seconds **********************")
    #     return await base64_to_pdf_bulk(labels)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"********************** FINISH time: {elapsed_time} seconds **********************")
    labelsPrint = await base64_to_pdf_bulk(labels)
    if labelsPrint is None:
        return JsonResponse({'message': 'No valid labels found'})
    return labelsPrint


async def async_proposals_and_courier(request, shipmentId, secret, commandId):
    # print('@@@@@@@@@@@@@@@@@@ async_proposals_and_courier SECRET @@@@@@@@@@@@@@@@@@@@', secret)
    pickupDateProposalId = await get_pickup_proposals(request, secret, shipmentId)
    if pickupDateProposalId:
        await get_courier(request, shipmentId, commandId, pickupDateProposalId, secret)


async def get_pickup_proposals(request, secret, shipmentId):

    async with httpx.AsyncClient() as client:
        try:
            url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/pickup-proposals" 
            headers = {'Authorization': f'Bearer {secret}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
            payload = {
                  "shipmentIds": [
                    shipmentId
                  ],
                #   "readyDate": ship_time
                }
            response = await client.post(url, headers=headers, json=payload)
            result = response.json()

            print('@@@@@@@@@ RESULT FOR PROPOSALS @@@@@@@@@', json.dumps(result, indent=4))
            print('@@@@@@@@@ RESPONSE PROPOSALS HEADERS 1 @@@@@@@@@', response.headers)
            # change_status(request, id, secret.account.name, 'SENT')
            # time.sleep(7)
            return  result[0]["proposals"][0]["proposalItems"][0]["id"] #"ANY"
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

    # return HttpResponse('ok')


async def get_courier(request, shipmentId, commandId, pickupDateProposalId, secret):

    # print('******************* GET COURIER SHIPMENTID ************************', shipmentId)
    # print('******************* pickupDateProposalId in GET COURIER ************************', pickupDateProposalId)
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/pickups/create-commands" 
            headers = {'Authorization': f'Bearer {secret}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
            payload = {
                      "commandId": commandId,
                      "input": {
                        "shipmentIds": [
                          shipmentId
                        ],
                        "pickupDateProposalId": pickupDateProposalId
                      }
                    }
            response = await client.post(url, headers=headers, json=payload)
            result = response.json()
            # if 'error' in result:
            #     error_code = result['error']
            #     if error_code == 'invalid_token':
            #         # print('ERROR RESULT @@@@@@@@@', error_code)
            #         try:
            #             # Refresh the token
            #             new_token = get_next_token(request, secret.refresh_token, 'retset')
            #             # Retry fetching orders with the new token
            #             return get_order_details(request, id)
            #         except Exception as e:
            #             print('Exception @@@@@@@@@', e)
            #             context = {'name': 'retset'}
            #             return render(request, 'invalid_token.html', context)
            print('RESULT FOR COURIER @@@@@@@@@', json.dumps(result, indent=4))
            print('@@@@@@@@@ RESPONSE COURIER HEADERS 1 @@@@@@@@@', response.headers)
            # change_status(request, id, secret.account.name, 'SENT')
            # time.sleep(7)
            # return get_shipment_status(request, result['commandId'], secret)
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

    return HttpResponse('ok')


async def label_print(request, shipmentId, secret):


    if shipmentId is not None:
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/label" 
                headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/octet-stream", 'Content-type': "application/vnd.allegro.public.v1+json"} 
                payload = {
                            "shipmentIds": [
                            shipmentId
                            ],
                            "pageSize": "A6",
                            # "cutLine": True
                        }
                response = await client.post(url, headers=headers, json=payload)

                print(' @@@@@@@@@ RESULT FOR LABELS shipmentId ZADZIAŁAŁO @@@@@@@@@ ', shipmentId)
                print(' @@@@@@@@@ RESULT FOR LABELS @@@@@@@@@ ', response)
                # print(' @@@@@@@@@ RESULT FOR LABELS @@@@@@@@@ ', response.content)
                # print('@@@@@@@@@ RESPONSE LABELS HEADERS 1 @@@@@@@@@', response.headers)
                return response.content
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    
    else:
        return None

    # return HttpResponse('ok')

    

def get_shipment_list(request):


    ids = request.GET.getlist('ids')
    # print('********************** IDS ****************************', ids)

    result = []

    for item in ids:
        parts = item.split(',')
        for part in parts:
            id, name, deliveryMethod = part.split('_')
            # result.append({'id': id, 'name': name, 'deliveryMethod': deliveryMethod})
    
            # print('********************** result ****************************', name)

            secret = Secret.objects.get(account__name=name)

            # print('********************** delivery_id ****************************', delivery_id)
            data = create_label(request, id, name)
            order_data = data[0]
            # print('********************** ORDER DATA IN SHIPMENT LIST****************************', order_data)
            # print('********************** order_data ****************************', order_data["delivery"]["method"]["id"])
            # print('********************** order_data ****************************', order_data["buyer"]["firstName"])
            # print('********************** order_data ****************************', order_data["buyer"]["companyName"])
            # print('********************** order_data ****************************', order_data["buyer"]["address"]["street"].split()[0])
            # print('********************** order_data ****************************', order_data["buyer"]["address"]["street"].split()[1])
            # print('********************** order_data ****************************', order_data["buyer"]["address"]["postCode"])
            # print('********************** order_data ****************************', order_data["buyer"]["address"]["city"])
            # print('********************** order_data ****************************', order_data["buyer"]["address"]["countryCode"])
            # print('********************** order_data ****************************', order_data["buyer"]["email"])
            # print('********************** order_data ****************************', order_data["delivery"]["address"]["phoneNumber"])



            for item in order_data['lineItems']:
                external_id = item['offer']['external']['id']
                offer_name = item['offer']["name"][:15]

            try:
                url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/shipments/create-commands"
                headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
                payload = {
                            # "commandId": "",
                            "input": {
                              "deliveryMethodId": order_data["delivery"]["method"]["id"],
                            #   "credentialsId": "c9e6f40a-3d25-48fc-838c-055ceb1c5bc0",
                              "sender": {
                                "name": "Jan Kowalski",
                                "company": "Allegro.pl sp. z o.o.",
                                "street": "Główna",
                                "streetNumber": "30",
                                "postalCode": "64-700",
                                "city": "Warszawa",
                                # "state": "AL",
                                "countryCode": "PL",
                                "email": "8awgqyk6a5+cub31c122@allegrogroup.pl",
                                "phone": "+48500600700",
                                # "point": ""
                              },
                              "receiver": {
                                "name": "Jan Kowalski", #order_data["buyer"]["firstName"],
                                "company": order_data["buyer"]["companyName"],
                                "street": order_data["buyer"]["address"]["street"].split()[0],
                                "streetNumber": order_data["buyer"]["address"]["street"].split()[1],
                                "postalCode": order_data["buyer"]["address"]["postCode"],
                                "city": order_data["buyer"]["address"]["city"],
                                # "state": "AL",
                                "countryCode": order_data["buyer"]["address"]["countryCode"],
                                "email": order_data["buyer"]["email"],
                                "phone": "+48500600700", #order_data["delivery"]["address"]["phoneNumber"],
                                # "point": ""
                              },
                              "pickup": { # Niewymagane, dane miejsca odbioru przesyłki
                                "name": "Jan Kowalski",
                                "company": "Allegro.pl sp. z o.o.",
                                "street": "Główna",
                                "streetNumber": 30,
                                "postalCode": "64-700",
                                "city": "Warszawa",
                                # "state": "AL",
                                "countryCode": "PL",
                                "email": "8awgqyk6a5+cub31c122@allegromail.pl",
                                "phone": "+48500600700",
                                # "point": "A1234567"
                              },
                              "referenceNumber": external_id,
                              "description": f'{offer_name}...',
                              "packages": [
                                {
                                  "type": "PACKAGE",
                                  "length": {
                                    "value": "16",
                                    "unit": "CENTIMETER"
                                  },
                                  "width": {
                                    "value": "16",
                                    "unit": "CENTIMETER"
                                  },
                                  "height": {
                                    "value": "16",
                                    "unit": "CENTIMETER"
                                  },
                                  "weight": {
                                    "value": "12.45",
                                    "unit": "KILOGRAMS"
                                  }
                                }
                              ],
                              "insurance": {
                                "amount": "23.47",
                                "currency": "PLN"
                              },
                            #   "cashOnDelivery": {
                            #     "amount": "2.50",
                            #     "currency": "PLN",
                            #     "ownerName": "Jan Kowalski",
                            #     "iban": "PL48109024022441789739167589"
                            #   },
                              "labelFormat": "PDF",
                              "additionalServices": [
                                "ADDITIONAL_HANDLING"
                              ],
                            #   "additionalProperties": {
                            #     "property1": "string",
                            #     "property2": "string"
                            #   }
                            }
                        }
                response = requests.post(url, headers=headers, json=payload)
                result = response.json()
                if 'error' in result:
                    error_code = result['error']
                    if error_code == 'invalid_token':
                        # print('ERROR RESULT @@@@@@@@@', error_code)
                        try:
                            # Refresh the token
                            new_token = get_next_token(request, secret.refresh_token, 'retset')
                            # Retry fetching orders with the new token
                            return get_order_details(request, id)
                        except Exception as e:
                            print('Exception @@@@@@@@@', e)
                            context = {'name': 'retset'}
                            return render(request, 'invalid_token.html', context)
                print('RESULT FOR SIPMENT LIST @@@@@@@@@', json.dumps(result, indent=4))
                print('@@@@@@@@@ RESPONSE HEADERS 1 @@@@@@@@@', response.headers)
                # change_status(request, id, secret.account.name, 'SENT')
                # time.sleep(7)
                return get_shipment_status(request, result['commandId'], secret)

            except requests.exceptions.HTTPError as err:
                raise SystemExit(err)

    # return HttpResponse('ok')


def get_shipment_status(request, commandId, secret):

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/shipments/create-commands/{commandId}"
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"} 
    
        response = requests.get(url, headers=headers)
        result = response.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token, 'retset')
                    # Retry fetching orders with the new token
                    return get_order_details(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    context = {'name': 'retset'}
                    return render(request, 'invalid_token.html', context)
        print('@@@@@@@@@ RESULT FOR SIPMENT STATUS @@@@@@@@@', json.dumps(result, indent=4))
        print('@@@@@@@@@ RESPONSE HEADERS 2 @@@@@@@@@', response.headers)
        time.sleep(10)
        pickupDateProposalId = get_pickup_proposals(secret.access_token, result["shipmentId"])
        return get_courier(request, result["shipmentId"], commandId, pickupDateProposalId, secret)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    
    return HttpResponse('ok')


