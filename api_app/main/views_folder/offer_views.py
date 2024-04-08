import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from ..utils import *
import requests
from ..models import *


def get_all_offers(request):

    account = Allegro.objects.get(user=request.user)
    secret = Secret.objects.get(account=account)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/sale/offers"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
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
                    return get_all_offers(request)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')
            
        # print('RESULT - get_all_offers - @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json()
        }
        return render(request, 'get_all_offers.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def get_one_offer(request, id):

    account = Allegro.objects.get(user=request.user)
    secret = Secret.objects.get(account=account)

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
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
                    return get_one_offer(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')
            
        print('RESULT - get_one_offer - @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json()
        }
        post_product_from_lister(request, result)
        return render(request, 'get_one_offer.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def post_product_from_lister(request, post_data):

    account = Allegro.objects.get(user=request.user)
    secret = Secret.objects.get(account=account)
    
    url = f'https://api.allegro.pl.allegrosandbox.pl/sale/product-offers'

    headers = {
        'Authorization': f'Bearer {secret.access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }

    response = requests.post(url, headers=headers, json=post_data)

    # print(response.status_code)
    # print(response.json())

    try:
        response_json = response.json()
        print("Response JSON:")
        print(response_json)
    except requests.exceptions.JSONDecodeError:
        print("No JSON response")

    # Additional error handling based on specific use case
    if response.status_code != 200:
        print(f"Error: {response.text}")

    return redirect('index')


def edit_offer_stock(request, id):

    account = Allegro.objects.get(user=request.user)
    secret = Secret.objects.get(account=account)

    data = json.loads(request.body.decode('utf-8'))
    new_stock = data.get('stock')

    print('**************new_stock**************', new_stock)
    patch_data = {
        "stock": {
        "available": new_stock,
        "unit": "UNIT"
        },
    }

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {
        'Authorization': f'Bearer {secret.access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }
        product_result = requests.patch(url, headers=headers, json=patch_data)
        result = product_result.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token)
                    # Retry fetching orders with the new token
                    return edit_offer_stock(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')
            
        print('RESULT - get_one_offer - @@@@@@@@@', json.dumps(result, indent=4))
        return JsonResponse(
                {
                    'message': 'Stock updated successfully',
                    'newValue': new_stock,
                }, 
                status=200,
            )
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)