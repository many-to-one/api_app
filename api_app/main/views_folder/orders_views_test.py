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


def get_orders(request, name):

    all_results = []
    result_with_name = []

    secret = Secret.objects.get(account__name=name)
    print('*********************** NAME get_orders **********************', secret.account.name)

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
        
    for result in all_results:
        for res in result["checkoutForms"]:
            result_with_name.append(res)
            # print('***************** RESULTS FOR PAGINATION *******************', json.dumps(res, indent=4))
    #         if res["fulfillment"]["status"] == 'NEW':

    #             print('***************** ALL RESULTS LOOP *******************', "NEW-tak")


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

    context = {
        'all_results': paginated_results, #sorted_results = sorted(all_results["checkoutForms"], key=lambda x: x["payment"]["finishedAt"])
        "name": name,
    }
    print('*********************** len all_results **********************', len(paginated_results))
    return render(request, 'get_all_orders.html', context)
    

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
        

def create_label_in_bulk_DPD(request):
    """
        This function get the description from **create_label_in_bulk()** and use it to post in
        DPD's labels creation. The description is a dict **all_post_data**, so that's why 
        we use here a loop to put in payload each dict's element.
    """

    ids = request.GET.getlist('ids')
    # print('********************** IDS ****************************', ids)

    result = []

    for item in ids:
        parts = item.split(',')
        for part in parts:
            id_, name = part.split('_')
            result.append({'id': id_, 'name': name})
    
    # print('********************** result ****************************', result)

    all_post_data = create_label_in_bulk(request, result)

    labels = []

    # print('********************** ALL DATA ****************************', json.dumps(all_post_data, indent=4))


    for post_data in all_post_data:

        # print('********************** BUYER ****************************', post_data['buyer']['firstName']) 
        secret = Secret.objects.get(account__name=post_data['name'])

        url = 'https://api-preprod.dpsin.dpdgroup.com:8443/shipping/v1/shipment?LabelPrintFormat=PDF&LabelPaperFormat=A6&qrcode=true&DropOffType=BOTH' #&LabelPrinterStartPosition=UPPER_LEFT
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {secret.dpd_access_token}',
            'Content-Type': 'application/json',
        }
        payload = [{
                    "shipmentInfos": {
                                     "productCode": "101"
                    },
                    "numberOfParcels": '1',#str(post_data['delivery']['calculatedNumberOfPackages']), 
                    "sender": {
                              "customerInfos": {
                                               "customerAccountNumber": "1495",
                                               "customerID": "1495"
                                               },
                              "address": {
                                         "name1" : "DPD Kraków",
                                         "country": "PL",
                                         "zipCode": "30-732",
                                         "city": "Kraków",
                                         "street": "Pułkownika Stanisława Dąbka 1A"
                                         }
                              },
                    "receiver": {
                                "address": {
                                "name1": post_data['result']['delivery']['address']['firstName'],  
                                "name2": post_data['result']['delivery']['address']['lastName'],
                                "country": post_data['result']['delivery']['address']['countryCode'],
                                "zipCode": post_data['result']['delivery']['address']['zipCode'],
                                "city": post_data['result']['delivery']['address']['city'],
                                "street": post_data['result']['delivery']['address']['street']
                                },
                    "contact": {
                               "phone1": post_data['result']['delivery']['address']['phoneNumber'],
                               "email": post_data['result']['buyer']['email'],
                               "contactPerson": post_data['result']['delivery']['address']['lastName']
                                },
                    "comment": "MY COMMENT"
                    },
                    "parcel": [{
                               "parcelInfos": {
                                              "weight": "6000"
                                              }
                              }]
                }]
        # time.sleep(1)
        
        response = requests.post(url, headers=headers, json=payload)
        # print('************** RESPONSE HEADERS ***********************', response.headers)
        if response.status_code == 401:
            # print('************** RESPONSE 401 ***********************')
            login_DPD(request)
        shipment = response.json()

        if response.status_code == 200:
            labels.append(shipment['label']['base64Data'])
            change_status(request, post_data['result']['id'], secret.account.name, 'SENT')
            # return base64_to_pdf(shipment['label']['base64Data'])
        
        if response.status_code == 400:
            return HttpResponse("DUPLICATED_PARCEL_SEARCH_KEY")
        
    # print('****************** LABELS *********************', labels)
    
    return base64_to_pdf_bulk(labels)


async def base64_to_pdf_bulk(base64_data_list):

    pdf_writer = PyPDF2.PdfWriter()

    try:
        for base64_data in base64_data_list:
            # print(' @@@@@@@@@@@@@@@@@ INSIDE base64_data @@@@@@@@@@@@@@@@@ ', base64_data)
            # Decode the Base64 data
            binary_data = base64_data #base64.b64decode(base64_data)
            # print(' @@@@@@@@@@@@@@@@@ INSIDE binary_data @@@@@@@@@@@@@@@@@ ', binary_data)

            # Create a PdfReader object
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(binary_data))
            # print(' @@@@@@@@@@@@@@@@@ INSIDE pdf_reader @@@@@@@@@@@@@@@@@ ', pdf_reader)

            # Merge each page from the PdfReader object into the PdfWriter object
            for page_num in range(len(pdf_reader.pages)):
                pdf_writer.add_page(pdf_reader.pages[page_num])

        # Create a BytesIO buffer to write the merged PDF
        output_buffer = io.BytesIO()
        print(' @@@@@@@@@@@@@@@@@ INSIDE output_buffer @@@@@@@@@@@@@@@@@ ', output_buffer)
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
            # print('@@@@@@@@@ PUNKT ODBIORU ID @@@@@@@@@', json.dumps(result, indent=4))
            print('@@@@@@@@@ CRETAE LABEL @@@@@@@@@')

            return result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def create_label_DPD(request, id):

    data = create_label(request, id)
    post_data = data[0]
    secret = data[1]

    for item in post_data['lineItems']:
        external_id = item['offer']['external']['id']
        quantity = item['quantity']

    if data:
        url = 'https://api-preprod.dpsin.dpdgroup.com:8443/shipping/v1/shipment?LabelPrintFormat=PDF&LabelPaperFormat=A6&qrcode=true&DropOffType=BOTH' #&LabelPrinterStartPosition=UPPER_LEFT
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {secret.dpd_access_token}',
            'Content-Type': 'application/json',
        }
        payload = [{
                    "shipmentInfos": {
                                     "productCode": "101"
                    },
                    "numberOfParcels": str(post_data['delivery']['calculatedNumberOfPackages']), #post_data['delivery']['calculatedNumberOfPackages']
                    "sender": {
                              "customerInfos": {
                                               "customerAccountNumber": "1495",
                                               "customerID": "1495"
                                               },
                              "address": {
                                         "name1" : "DPD Kraków",
                                         "country": "PL",
                                         "zipCode": "30-732",
                                         "city": "Kraków",
                                         "street": "Pułkownika Stanisława Dąbka 1A"
                                         }
                              },
                    "receiver": {
                                "address": {
                                "name1": post_data['delivery']['address']['firstName'],  
                                "name2": post_data['delivery']['address']['lastName'],
                                "country": post_data['delivery']['address']['countryCode'],
                                "zipCode": post_data['delivery']['address']['zipCode'],
                                "city": post_data['delivery']['address']['city'],
                                "street": post_data['delivery']['address']['street']
                                },
                    "contact": {
                               "phone1": post_data['delivery']['address']['phoneNumber'],
                               "email": post_data['buyer']['email'],
                               "contactPerson": post_data['delivery']['address']['lastName']
                                },
                    "comment": f'{external_id} - {quantity}szt'
                    },
                    "parcel": [{
                               "parcelInfos": {
                                              "weight": "6000"
                                              }
                              }]
                }]
        
        response = requests.post(url, headers=headers, json=payload)
        print('************** RESPONSE HEADERS ***********************', response.headers)
        if response.status_code == 401:
            # print('************** RESPONSE 401 ***********************')
            login_DPD(request)
        shipment = response.json()

        if response.status_code == 200:
            change_status(request, post_data['id'], secret.account.name, 'SENT')
            return base64_to_pdf(shipment['label']['base64Data'])
        
        if response.status_code == 400:
            return HttpResponse("DUPLICATED_PARCEL_SEARCH_KEY")

    # return HttpResponse('ok')


def base64_to_pdf(base64_data):

    print('************** RESPONSE base64_data ***********************', base64_data[20])

    try:
        # Decode the Base64 data
        binary_data = base64.b64decode(base64_data)

        # Set the appropriate content type for PDF
        response = HttpResponse(binary_data, content_type='application/pdf')

        # Optionally, set a filename for the downloaded file
        response['Content-Disposition'] = 'inline; filename="output.pdf"'
        return response
    
    except Exception as e:
        print("Error:", e)


def login_DPD (request):
    print('*********** LOGIN DPD CALLED ***********')

    try:
        url = 'https://api-preprod.dpsin.dpdgroup.com:8443/shipping/v1/login'
        # url = 'https://api-preprod.dpsin.dpdgroup.com:8443/v1/auth/tokens'
        headers = {
            'X-DPD-LOGIN':'test',
            'X-DPD-PASSWORD': 'thetu4Ee',
            'X-DPD-BUCODE': '021'
        }
        response = requests.post(url, headers=headers)
        print('*********** LOGIN DPD STATUS ***********', response.status_code)
        # print('*********** LOGIN RESPONSE JSON ***********', response.json())
        print('*********** LOGIN RESPONSE HEADERS ***********', response.headers)
        accounts = Allegro.objects.filter(user=request.user)
        for account in accounts:
            secret = Secret.objects.get(account=account)
            secret.dpd_access_token = response.headers['x-dpd-token']
            secret.save()
    except:
        print('*********** COŚ POSZŁO NIE TAK ***********')
    


#################################################################################################################################
############################################# THE END OF DPD'S LABELS LOGIC #####################################################
#################################################################################################################################




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
    return await create_label(request, id, name, secret), await get_offer_descr(request, offerId, secret)


async def set_shipment_list_async(request, ids):

    tasks = []
    secret = await sync_to_async(Secret.objects.get)(account__name='retset')
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
async def get_secret():
    secret = sync_to_async(Secret.objects.get)(account__name='retset')
    return await secret


async def set_shipment_list_q(results, secret):
    # start_time = time.time()

    print('********************** set_shipment_list_q results ****************************', results)
    print('********************** set_shipment_list_q secret ****************************', secret)
    # print('********************** results[0] ****************************', results[0])
    # print('********************** results[1] ****************************', results[1])

    from ..utils import pickup_point_order, no_pickup_point_order, cash_no_point_order, test
    # secret = Secret.objects.get(account__name='retset')
    # secret = await sync_to_async(Secret.objects.get)(account__name='retset')
    # secret = await get_secret()
    # ids = request.GET.getlist('ids')
    # print('********************** secret + ****************************', secret)

    # pickup = request.GET.getlist('pickup')
    tasks = []

    # for order_data in results:
    #     if isinstance(order_data, tuple):
    #         dict_data.update(order_data[0])
    #         print(
    #                 '********************** NAME +++ tuple ****************************', 
    #                 dict_data
    #             )
        # elif isinstance(order_data, list):
        #     dict_data['descr'].extend(order_data)
        #     print('******************* NAME +++ list **********************')        


    # print('******************* dict_data 1 **********************', dict_data['lineItems'][0]['offer']['external']['id'])
    # print('******************* dict_data 2 **********************', dict_data['descr'])   
    # print('******************* dict_data **********************', dict_data) 
    # print('******************* descri **********************', descri) 


    # data_r = [
    #     {'key_1': 'val_1'}, {'key_2': 'val_2'},
    #     ]

    if results:
        
            [
                tasks.append(asyncio.create_task(
                test(
                    secret, 
                    order_data[0],
                    order_data[0]['lineItems'][0]['offer']['external']['id'],
                    order_data[0]['lineItems'][0]['offer']["name"][:15],
                    order_data[1]
                )
                ))
                for order_data in results
                if isinstance(order_data, tuple)
            ]

        # result_arr = [
        #     tasks.append(asyncio.create_task(
        #         # pickup_point_order(
        #         test(
        #             secret=secret, 
        #             order_data=order_data, 
        #             # a=dict_data['lineItems'][0]['offer']['external']['id'], 
        #             # b=dict_data['lineItems'][0]['offer']["name"][:15], 
        #             # descr=dict_data['descr']
        #         )
        #         for order_data in dict_data
        #         ))
        #     ]

        # result_arr = [
        #     tasks.append(asyncio.create_task(
        #         # pickup_point_order(
        #         test(
        #             secret=secret, 
        #             order_data=order_data[0], 
        #             a=order_data[0]['lineItems'][0]['offer']['external']['id'], 
        #             b=order_data[0]['lineItems'][0]['offer']["name"][:15], 
        #             descr=order_data if isinstance(order_data, dict) else None,
        #         )
        #         ))
        #     for order_data in results
        #     # if isinstance(order_data, tuple)
        #     ]
        
    # result_arr = [
    #     tasks.append(asyncio.create_task(test(string='string', data=data,)))
    #     for data in data_r
    #     ]
    
    
    # for data in data_r:
    #     a = test(string='string',data=data)
    #     result_arr.append(a)

    # print('********************** NAME + ****************************', results)

    # for order_data in results:
    #     if order_data is not None:
    #         if isinstance(order_data, tuple):
    #             for item in order_data[0]['lineItems']:
    #                 external_id = item['offer']['external']['id']
    #                 offer_name = item['offer']["name"][:15]
    #                 order_data = order_data[0]

    #                 try:
    #                     if order_data["delivery"]["pickupPoint"] == None:
    #                         if order_data["payment"]["type"] == 'CASH_ON_DELIVERY': 
    #                             result = cash_no_point_order(secret, order_data, external_id, offer_name, descr)
    #                         else:
    #                             result = no_pickup_point_order(secret,  order_data, external_id, offer_name, descr)
    #                     else:
    #                         if order_data["payment"]["type"] == 'CASH_ON_DELIVERY': 
    #                             result = cash_no_point_order(secret,  order_data, external_id, offer_name, descr)
    #                         # print('********************** pickupPoint ****************************', order_data["delivery"]["pickupPoint"])
    #                         else:
    #                             # result = pickup_point_order(secret,  order_data, external_id, offer_name, descr)
    #                             result = tasks.append(asyncio.create_task(pickup_point_order(secret,  order_data, external_id, offer_name, descr)))
    #                     if 'error' in result:
    #                         error_code = result['error']
    #                         if error_code == 'invalid_token':
    #                             # print('ERROR RESULT @@@@@@@@@', error_code)
    #                             try:
    #                                 # Refresh the token
    #                                 new_token = get_next_token(request, secret.refresh_token, 'retset')
    #                                 # Retry fetching orders with the new token
    #                                 return get_order_details(request, id)
    #                             except Exception as e:
    #                                 print('Exception @@@@@@@@@', e)
    #                                 context = {'name': 'retset'}
    #                                 return render(request, 'invalid_token.html', context)
    #                     # print('RESULT FOR SIPMENT LIST @@@@@@@@@', json.dumps(result, indent=4))
    #                     # print('@@@@@@@@@ RESPONSE HEADERS 1 @@@@@@@@@', response.headers)
    #                     result_arr.append({"id": id, "commandId": result["commandId"], "name": 'retset'})
    #                             # return get_shipment_status(request, result['commandId'], secret
    #                 except requests.exceptions.HTTPError as err:
    #                     raise SystemExit(err)

            # else:
            #     continue
    # labels = await asyncio.gather(*tasks)
    

    # return HttpResponse('ok')
    return await asyncio.gather(*tasks)


# @sync_to_async
def set_shipment_list(request):

    start_time = time.time()

    ids = request.GET.getlist('ids')
    # print('********************** IDS set_shipment_list IDS ****************************', ids)

    pickup = request.GET.getlist('pickup')
    secret = Secret.objects.get(account__name='retset')
    # time.sleep(2)
    print('********************** secret @@@ ****************************', secret)
    # secret = await sync_to_async(Secret.objects.get)(account__name='retset')
    results = asyncio.run(set_shipment_list_async(request, ids))#[0]
    # print('********************** /// results /// ****************************', results)  #results[1][1]
    # time.sleep(1)
    if results:
        if secret:
            results_ = asyncio.run(set_shipment_list_q(results, secret))
            # print('**********************  /// results_secret /// ****************************', secret)

    context = {
        'result': results_,
        'name': 'retset',
        }
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"********************** set_shipment_list finished time: {elapsed_time} seconds **********************")

    return render(request, 'set_pickup.html', context)

    # return HttpResponse('ok')


async def make_order(request, secret, commandId):

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
    # print('@@@@@@@@@ RESULT FOR SHIPMENT STATUS ID @@@@@@@@@', json.dumps(result, indent=4))
    return result


async def get_shipment_status_id(request):

    start_time = time.time()
    tasks = []
    while True:
        labels = []
        ids = request.GET.getlist('ids')
        pickup = request.GET.getlist('pickup')
        print('@@@@@@@@@ ids @@@@@@@@@', ids)

        time.sleep(5)
        print('********************** TIME TIME TIME 5 SECONDS ****************************')
        for item in ids:
            parts = item.split(',')
            for part in parts:
                commandId, name = part.split(':')
                # secret = Secret.objects.get(account__name=name)
                secret = await sync_to_async(Secret.objects.get)(account__name='retset')

                try:
                    result = await make_order(request, secret, commandId)
                    if result["status"] == "ERROR":
                        print('*************** ERROR ERROR ERROR ***************')
                        print(result["status"])
                        print(result["errors"][0]["userMessage"])
                        continue
                        # return JsonResponse({
                        #     "ERROR": result["errors"][0]["userMessage"]
                        # })

                    if result["shipmentId"] == None:
                        # makes this function restart and returns ONLY ONCE
                        break

                    if pickup[0] == 'pickup':                  
                        # shipmentId = result["shipmentId"]
                        # loop = asyncio.new_event_loop()
                        # asyncio.set_event_loop(loop)
                        # loop.run_until_complete(async_operations(request, shipmentId, secret, commandId))
                        pickupDateProposalId = get_pickup_proposals(request, secret.access_token, result["shipmentId"])
                        get_courier(request, result["shipmentId"], commandId, pickupDateProposalId, secret)
                    if result["shipmentId"] is not None:
                        label =  tasks.append(asyncio.create_task(label_print(request, result["shipmentId"], secret)))
                        # label = await label_print(request, result["shipmentId"], secret)
                        # labels.append(label)

                except requests.exceptions.HTTPError as err:
                    raise SystemExit(err)
        labels = await asyncio.gather(*tasks)

        if any(label is not None for label in labels):
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"********************** FINISH time: {elapsed_time} seconds **********************")
            return await base64_to_pdf_bulk(labels)




async def async_operations(request, shipmentId, secret, commandId):
    pickupDateProposalId = await get_pickup_proposals(request, secret.access_token, shipmentId)
    await get_courier(request, shipmentId, commandId, pickupDateProposalId, secret)


def get_pickup_proposals(request, token, shipmentId):

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/pickup-proposals" 
        headers = {'Authorization': f'Bearer {token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
        payload = {
              "shipmentIds": [
                shipmentId
              ],
            #   "readyDate": ship_time
            }
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
    
        print('@@@@@@@@@ RESULT FOR PROPOSALS @@@@@@@@@', json.dumps(result, indent=4))
        print('@@@@@@@@@ RESPONSE PROPOSALS HEADERS 1 @@@@@@@@@', response.headers)
        # change_status(request, id, secret.account.name, 'SENT')
        # time.sleep(7)
        return  result[0]["proposals"][0]["proposalItems"][0]["id"] #"ANY"
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    # return HttpResponse('ok')


def get_courier(request, shipmentId, commandId, pickupDateProposalId, secret):

    # print('******************* GET COURIER SHIPMENTID ************************', shipmentId)
    # print('******************* pickupDateProposalId in GET COURIER ************************', pickupDateProposalId)

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/pickups/create-commands" 
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
        payload = {
                  "commandId": commandId,
                  "input": {
                    "shipmentIds": [
                      shipmentId
                    ],
                    "pickupDateProposalId": pickupDateProposalId
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
        print('RESULT FOR COURIER @@@@@@@@@', json.dumps(result, indent=4))
        print('@@@@@@@@@ RESPONSE COURIER HEADERS 1 @@@@@@@@@', response.headers)
        # change_status(request, id, secret.account.name, 'SENT')
        # time.sleep(7)
        # return get_shipment_status(request, result['commandId'], secret)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    return HttpResponse('ok')


async def label_print(request, shipmentId, secret):


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


