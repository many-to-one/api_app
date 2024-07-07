import csv
import io
import json, requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from .offer_views import get_all_offers
from ..utils import *
from ..models import *
import uuid

def bulk_edit(request, name, ed_value):

    if request.user.is_authenticated:

        ids = request.GET.getlist('ids')
        encoded_offers = ','.join(ids)
        print('********************** ids ****************************', ids)

        return redirect(f'{ed_value}', name=name, offers=encoded_offers)


def PRICE(request, name, offers):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)
        commandId = uuid.uuid4()
        offers_list = [{'id': offer_id} for offer_id in offers.split(',')]

        if request.method == 'POST':
            price = request.POST.get('price')
            percent = request.POST.get('percent')

            print('********************** offers_list ****************************', len(offers_list))
            print('********************** price ****************************', price)
            print('********************** percent ****************************', percent)

            data = {
                "modification": {
                    "type": "FIXED_PRICE",
                    "marketplaceId": "allegro-pl",
                    "price" : {
                        "amount": price,
                        "currency": "PLN",
                    }
                },
                "offerCriteria": [
                    {
                    "offers": offers_list,
                    "type": "CONTAINS_OFFERS"
                    },
                ]
            }

            data = {
                "modification": {
                    "type": "INCREASE_PERCENTAGE",
                    "marketplaceId": "allegro-pl",
                    "percentage" : percent,
                },
                "offerCriteria": [
                    {
                    "offers": offers_list,
                    "type": "CONTAINS_OFFERS"
                    }
                ]
            }

            try:
                url = f"https://api.allegro.pl.allegrosandbox.pl/sale/offer-price-change-commands/{commandId}"
                # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
                headers = {
                    'Authorization': f'Bearer {secret.access_token}', 
                    'Accept': "application/vnd.allegro.public.v1+json",
                    'Content-Type': "application/vnd.allegro.public.v1+json",
                    }
                product_result = requests.put(url, headers=headers, json=data)
                result = product_result.json()
                # print('******* product_result ********', result)
                if 'error' in result:
                    error_code = result['error']
                    if error_code == 'invalid_token':
                        # print('ERROR RESULT @@@@@@@@@', error_code)
                        try:
                            # Refresh the token
                            new_token = get_next_token(request, secret.refresh_token, name)
                            # Retry fetching orders with the new token
                            return get_all_offers(request, name)
                        except Exception as e:
                            print('Exception @@@@@@@@@', e)
                            context = {'name': name}
                            return render(request, 'invalid_token.html', context)
                print('RESULT - PRICE - @@@@@@@@@', json.dumps(result, indent=4))
                context = {
                    'result': product_result.json(),
                    'name': name,
                }
                return redirect('get_all_offers', name=name)
            except requests.exceptions.HTTPError as err:
                raise SystemExit(err)


        return render(request, 'bulk_price.html')



def QUANTITY(request, name, offers):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)
        commandId = uuid.uuid4()
        offers_list = [{'id': offer_id} for offer_id in offers.split(',')]

        if request.method == 'POST':
            quantity = request.POST.get('quantity')

            print('********************** offers_list ****************************', offers_list)
            print('********************** quantity ****************************', quantity)

            data = {
                "modification": {
                    "changeType": "FIXED",
                    "value": quantity,
                },
                "offerCriteria": [
                    {
                    "offers": offers_list,
                    "type": "CONTAINS_OFFERS"
                    }
                ]
            }


            try:
                url = f"https://api.allegro.pl.allegrosandbox.pl/sale/offer-quantity-change-commands/{commandId}"
                # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
                headers = {
                    'Authorization': f'Bearer {secret.access_token}', 
                    'Accept': "application/vnd.allegro.public.v1+json",
                    'Content-Type': "application/vnd.allegro.public.v1+json",
                    }
                product_result = requests.put(url, headers=headers, json=data)
                result = product_result.json()
                # print('******* product_result ********', result)
                if 'error' in result:
                    error_code = result['error']
                    if error_code == 'invalid_token':
                        # print('ERROR RESULT @@@@@@@@@', error_code)
                        try:
                            # Refresh the token
                            new_token = get_next_token(request, secret.refresh_token, name)
                            # Retry fetching orders with the new token
                            return get_all_offers(request, name)
                        except Exception as e:
                            print('Exception @@@@@@@@@', e)
                            context = {'name': name}
                            return render(request, 'invalid_token.html', context)
                print('RESULT - PRICE - @@@@@@@@@', json.dumps(result, indent=4))
                context = {
                    'result': product_result.json(),
                    'name': name,
                }
                return redirect('get_all_offers', name=name)
            except requests.exceptions.HTTPError as err:
                raise SystemExit(err)


        return render(request, 'bulk_quantity.html')