import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
import requests
import os
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
    return render(request, 'get_orders.html', context)
    

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

    print('********************** DATA ****************************', secret)
    print('********************** BUYER ****************************', post_data['buyer']['firstName'])

    if data:
        url = 'https://api-preprod.dpsin.dpdgroup.com:8443/shipping/v1/shipment?LabelPrintFormat=PDF&LabelPaperFormat=A6&qrcode=true&DropOffType=BOTH' #&LabelPrinterStartPosition=UPPER_LEFT
        headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJwYXNzd29yZCI6InRoZXR1NEVlIiwiYnVDb2RlIjoiMDIxIiwidXNlck5hbWUiOiJ0ZXN0IiwiZXhwIjoxNzEzODgyMTMwfQ.S90vgHOpkc0uWt6dCCqw6zW5DPb4RI7w7pNLcRA3RpCvtkKmNLe3qQ2A9WF_Y9RPzWj6TOetCGHW9OSbReh-vg',
            'Content-Type': 'application/json',
        }
        payload = [{
                    "shipmentInfos": {
                                     "productCode": "101"
                    },
                    "numberOfParcels": post_data['delivery']['calculatedNumberOfPackages'],
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
                    "comment": "commentaire"
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
            login_DPD(data.secret)
        shipment = response.json()

        if response.status_code == 200:
            return base64_to_pdf(shipment['label']['base64Data'])
        
        if response.status_code == 400:
            return HttpResponse("DUPLICATED_PARCEL_SEARCH_KEY")

    # return HttpResponse('ok')



def base64_to_pdf(base64_data):

    import base64

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


def login_DPD (secret):
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
        print('*********** LOGIN RESPONSE JSON ***********', response.json())
        print('*********** LOGIN RESPONSE HEADERS ***********', response.headers)
        # secret.dpd
    except:
        print('*********** COŚ POSZŁO NIE TAK ***********')
    


def change_status(request, id, name):

    account = Allegro.objects.get(name=name)

    secret = Secret.objects.get(account=account)

    data = json.loads(request.body.decode('utf-8'))
    new_status = data.get('status')
    
    print('*********** new_status ***********', new_status, name)
    print('*********** secret.access_token ***********', secret.account.name)
    # print('*********** secret.access_token ***********', secret.access_token)

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{id}/fulfillment"
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': 'application/vnd.allegro.public.v1+json', 'Content-Type': 'application/vnd.allegro.public.v1+json'}

        data = {
                "status": new_status,
                "shipmentSummary": {
                "lineItemsSent": "SOME"
                }
            }

        response = requests.put(url, headers=headers, json=data)
        print('*********** change_status ***********', response)
        # result = response.json()
        # print('*********** response.json() ***********', result)

        return JsonResponse(
                {
                    'message': 'Stock updated successfully',
                    'newStatus': new_status,
                }, 
                status=200,
            )
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)