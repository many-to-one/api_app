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


def get_orders(request):

    all_results = []
    result_with_name = {}
    accounts = Allegro.objects.filter(user=request.user)
    for account in accounts:
        secret = Secret.objects.get(account=account)
        print('*********************** NAME get_orders **********************', secret.account.name)

        try:
            url = "https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms"
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            # print('***********************secret.access_token**********************', secret.access_token)
            product_result = requests.get(url, headers=headers, verify=True)
            result = product_result.json()
            print('************* TYPE *************', type(result))
            # result_with_name = {
            #     all_results: result,
            #     'name': secret.account.name
            # }
            result.update({'name': secret.account.name})
            all_results.append(result)
            # all_results.append(result)
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, account.name)
                        # Retry fetching orders with the new token
                        return get_orders(request)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': account.name}
                        return render(request, 'invalid_token.html', context)
            # print('*********************** result **********************', json.dumps(result, indent=4))
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

    context = {
        'all_results': all_results
    }
    # print('*********************** all_results **********************', all_results)
    return render(request, 'get_all_orders.html', context)
    

def get_order_details(request, id):

    accounts = Allegro.objects.filter(user=request.user)
    for account in accounts:
        secret = Secret.objects.get(account=account)

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
                        new_token = get_next_token(request, secret.refresh_token, account.name)
                        # Retry fetching orders with the new token
                        return get_order_details(request, id)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': account.name}
                        return render(request, 'invalid_token.html', context)

            print('RESULT @@@@@@@@@', json.dumps(result, indent=4))
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


def base64_to_pdf_bulk(base64_data_list):

    pdf_writer = PyPDF2.PdfWriter()

    try:
        for base64_data in base64_data_list:
            # Decode the Base64 data
            binary_data = base64.b64decode(base64_data)

            # Create a PdfReader object
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(binary_data))

            # Merge each page from the PdfReader object into the PdfWriter object
            for page_num in range(len(pdf_reader.pages)):
                pdf_writer.add_page(pdf_reader.pages[page_num])

        # Create a BytesIO buffer to write the merged PDF
        output_buffer = io.BytesIO()
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

def create_label(request, id):

    print('********************** CREATE LABEL CALLED ****************************', id)

    accounts = Allegro.objects.filter(user=request.user)
    for account in accounts:
        secret = Secret.objects.get(account=account)

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
                        new_token = get_next_token(request, secret.refresh_token, account.name)
                        # Retry fetching orders with the new token
                        return get_order_details(request, id)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': account.name}
                        return render(request, 'invalid_token.html', context)
            print('RESULT FOR DPD @@@@@@@@@', json.dumps(result, indent=4))
            # create_label(result)
            return result, secret
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)



def create_label_DPD(request, id):

    data = create_label(request, id)
    post_data = data[0]
    secret = data[1]

    # print('********************** DATA ****************************', secret)
    # print('********************** BUYER ****************************', post_data['buyer']['firstName'])
    for item in post_data['lineItems']:
        external_id = item['offer']['external']['id']
        quantity = item['quantity']
        # print("External ID:", external_id)
        # print("Quantity:", quantity)

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




def change_status(request, id, name, status):

    account = Allegro.objects.get(name=name)

    secret = Secret.objects.get(account=account)

    # data = json.loads(request.body.decode('utf-8'))
    # new_status = data.get('status')
    
    print('*********** new_status ***********', status, name)
    print('*********** secret.account.name ***********', secret.account.name)
    print('*********** secret.access_token ***********', secret.access_token)

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
        print('*********** change_status ***********', response)
        # result = response.json()
        # print('*********** change_status response.json() ***********', result)

        return JsonResponse(
                {
                    'message': 'Stock updated successfully',
                    'newStatus': status,
                }, 
                status=200,
            )
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def get_shipment_id(request, secret, name, deliveryMethod):
     
    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/delivery-services"
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
         #print('RESULT FOR DPD @@@@@@@@@', json.dumps(result, indent=4))
        for r in result['services']:
            # print('************ LOOP ID ************', r['id'])
            # print('************ LOOP NAME ************', r['name'])
            if r['name'] == deliveryMethod and r['marketplaces'] == ['allegro-pl']:
                # print('************ Allegro Kurier DPD ID ************', r['name'], '----', r['id']['deliveryMethodId'], '----', r['marketplaces'])
                return r['id']['deliveryMethodId']
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    # return HttpResponse('ok')
    

def get_shipment_list(request):

    # accounts = Allegro.objects.filter(user=request.user)
    # for account in accounts:
    # secret = Secret.objects.get(account__name='retset')

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

            # delivery_id = get_shipment_id(request, secret, name, deliveryMethod)
            # print('********************** delivery_id ****************************', delivery_id)
            data = create_label(request, id)
            order_data = data[0]
            # print('********************** order_data ****************************', json.dumps(order_data, indent=4))
            print('********************** order_data ****************************', order_data["delivery"]["method"]["id"])
            print('********************** order_data ****************************', order_data["buyer"]["firstName"])
            print('********************** order_data ****************************', order_data["buyer"]["companyName"])
            print('********************** order_data ****************************', order_data["buyer"]["address"]["street"].split()[0])
            print('********************** order_data ****************************', order_data["buyer"]["address"]["street"].split()[1])
            print('********************** order_data ****************************', order_data["buyer"]["address"]["postCode"])
            print('********************** order_data ****************************', order_data["buyer"]["address"]["city"])
            print('********************** order_data ****************************', order_data["buyer"]["address"]["countryCode"])
            print('********************** order_data ****************************', order_data["buyer"]["email"])
            print('********************** order_data ****************************', order_data["delivery"]["address"]["phoneNumber"])



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
                            #   "pickup": { # Niewymagane, dane miejsca odbioru przesyłki
                            #     "name": "Jan Kowalski",
                            #     "company": "Allegro.pl sp. z o.o.",
                            #     "street": "Główna",
                            #     "streetNumber": 30,
                            #     "postalCode": "10-200",
                            #     "city": "Warszawa",
                            #     "state": "AL",
                            #     "countryCode": "PL",
                            #     "email": "8awgqyk6a5+cub31c122@allegromail.pl",
                            #     "phone": 500600700,
                            #     "point": "A1234567"
                            #   },
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
                time.sleep(7)
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
        # return result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    
    return HttpResponse('ok')