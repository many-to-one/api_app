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

    account = Allegro.objects.get(user=request.user)
    secret = Secret.objects.get(account=account)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms"
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token)
                    # Retry fetching orders with the new token
                    return get_orders(request)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')

        # print('RESULT @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json()
        }
        return render(request, 'get_orders.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def get_order_details(request, id):

    account = Allegro.objects.get(user=request.user)
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
                    new_token = get_next_token(request, secret.refresh_token)
                    # Retry fetching orders with the new token
                    return get_order_details(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')

        # print('RESULT @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'order': product_result.json()
        }
        return render(request, 'get_order_details.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    


def change_status(request, id):

    account = Allegro.objects.get(user=request.user)
    secret = Secret.objects.get(account=account)

    data = json.loads(request.body.decode('utf-8'))
    new_status = data.get('status')

    print('*********** new_status ***********', new_status)

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{id}/fulfillment"
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': 'application/vnd.allegro.public.v1+json', 'Content-Type': 'application/vnd.allegro.public.v1+json'}
         
        data = {
                "status": "CANCELLED",
                # "shipmentSummary": {
                # "lineItemsSent": "SOME"
                # }
            }
        
        response = requests.put(url, headers=headers, json=data)
        print('*********** change_status ***********', response)
        # result = response.json()
        # if 'error' in result:
        #     error_code = result['error']
        #     if error_code == 'invalid_token':
        #         # print('ERROR RESULT @@@@@@@@@', error_code)
        #         try:
        #             # Refresh the token
        #             new_token = get_next_token(request, secret.refresh_token)
        #             # Retry fetching orders with the new token
        #             return change_status(request, id)
        #         except Exception as e:
        #             print('Exception @@@@@@@@@', e)
        #             return redirect('invalid_token')

        # print('*********** change_status ***********', json.dumps(result, indent=4))

        return JsonResponse(
                {
                    'message': 'Stock updated successfully',
                    'newStatus': new_status,
                }, 
                status=200,
            )
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)