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
            return result
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)


def create_label_DPD(request, id):

    data = create_label(request, id)
    # data = False

    print('********************** DATA ****************************', data)

    if data:
        url = 'https://api-preprod.dpsin.dpdgroup.com:8443/shipping/v1/shipment?LabelPrintFormat=PDF&LabelPaperFormat=A5&LabelPrinterStartPosition=UPPER_LEFT&qrcode=true&DropOffType=BOTH'
        headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJwYXNzd29yZCI6InRoZXR1NEVlIiwiYnVDb2RlIjoiMDIxIiwidXNlck5hbWUiOiJ0ZXN0IiwiZXhwIjoxNzEzODA5MjI4fQ.4D34gIdHXvZ5U27hAF-aWnI3wUEo6Nr1F-lSAEPP7oGqCo-8Nk-YmA-b0EZBm3ahyGQ4m6etM8eqlzE4Cn6fpQ',
            'Content-Type': 'application/json',
        }
        payload = [{
            "shipmentInfos": {
                "productCode": "101"
            },
            "numberOfParcels": "1",
            "sender": {
                "customerInfos": {
                    "customerAccountNumber": "1495",
                    "customerID": "1495"
                },
                "address": {
                    "name1": "DPD Kraków",
                    "country": "PL",
                    "zipCode": "30-732",
                    "city": "Kraków",
                    "street": "Pułkownika Stanisława Dąbka 1A"
                }
            },
            "receiver": {
                "address": {
                    "name1": "DPD Warszawa",
                    "name2": "DPD Person Name",
                    "country": "PL",
                    "zipCode": "02-274",
                    "city": "Warszawa",
                    "street": "Mineralna 15"
                },
                "contact": {
                    "phone1": "0123456789",
                    "email": "a@a.com",
                    "contactPerson": "DPD Contact"
                }
            },
            "comment": "commentaire",
            "parcel": [{
                "parcelInfos": {
                    "weight": "6000"
                }
            }]
        }]
        response = requests.post(url, headers=headers, json=payload)
        shipment = response.json()

        if shipment:
            # output_file = "../../dpd_label.pdf"
            base64_to_pdf(shipment['label']['base64Data'])

    # print("Shipment created successfully.", shipment['label']['base64Data'])


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

    # return HttpResponse('Ok')
    


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