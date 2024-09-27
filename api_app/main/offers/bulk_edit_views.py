import csv
import io
import json, requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from .offer_views import get_all_offers, download_all_offers
from ..utils import *
from ..models import *
import uuid
from ..api_service import sync_service


def bulk_edit(request, name, ed_value):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)

        ids = request.GET.getlist('ids')
        encoded_offers = ','.join(ids)
        print('********************** ids ****************************', ids)
        print('********************** ed_value ****************************', ed_value)

        if ed_value == 'JSON_OFFERS':
            result = asyncio.run(download_all_offers(request, ids, secret.access_token))
            buffer = io.BytesIO()
            json_string = json.dumps(result, indent=4)
            buffer.write(json_string.encode('utf-8'))
            buffer.seek(0)

            # Serve the file as a downloadable response
            response = HttpResponse(buffer, content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{name}_offers.json"'
            return response
        else:
            return redirect(f'{ed_value}', name=name, secret=secret.access_token, offers=encoded_offers)


def PRICE(request, name, secret, offers):

    if request.user.is_authenticated:

        # secret = Secret.objects.get(account__name=name)
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



def QUANTITY(request, name, secret, offers):

    if request.user.is_authenticated:

        # secret = Secret.objects.get(account__name=name)
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

            url = f"sale/offer-quantity-change-commands/{commandId}"
            debug_name = 'QUANTITY 124'

            offers = sync_service.Offers(name)
            result = offers.put_(request, url, data, debug_name)

            context = {
                    'result': result,
                    'name': name,
                }
            return redirect('get_all_offers', name=name)
            


            # try:
            #     url = f"https://api.allegro.pl.allegrosandbox.pl/sale/offer-quantity-change-commands/{commandId}"
            #     # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
            #     headers = {
            #         'Authorization': f'Bearer {secret}', 
            #         'Accept': "application/vnd.allegro.public.v1+json",
            #         'Content-Type': "application/vnd.allegro.public.v1+json",
            #         }
            #     product_result = requests.put(url, headers=headers, json=data)
            #     result = product_result.json()
            #     print('******* QUANTITY ********', result)
            #     if 'error' in result:
            #         error_code = result['error']
            #         if error_code == 'invalid_token':
            #             # print('ERROR RESULT @@@@@@@@@', error_code)
            #             try:
            #                 # Refresh the token
            #                 new_token = get_next_token(request, secret.refresh_token, name)
            #                 # Retry fetching orders with the new token
            #                 return get_all_offers(request, name)
            #             except Exception as e:
            #                 print('Exception @@@@@@@@@', e)
            #                 context = {'name': name}
            #                 return render(request, 'invalid_token.html', context)
            #     print('RESULT - PRICE - @@@@@@@@@', json.dumps(result, indent=4))
            #     context = {
            #         'result': product_result.json(),
            #         'name': name,
            #     }
            #     return redirect('get_all_offers', name=name)
            # except requests.exceptions.HTTPError as err:
            #     raise SystemExit(err)


        return render(request, 'bulk_quantity.html')
    

def all_shipping_rates(request, name, secret,):

    if request.user.is_authenticated:

        try:
            url = f"https://api.allegro.pl.allegrosandbox.pl/sale/shipping-rates" 
            # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
            headers = {
                'Authorization': f'Bearer {secret}', 
                'Accept': "application/vnd.allegro.public.v1+json",
                'Content-Type': "application/vnd.allegro.public.v1+json",
                }
            product_result = requests.get(url, headers=headers)
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
            print('RESULT - all_shipping_rates json - @@@@@@@@@', json.dumps(result, indent=4))
            
            return product_result.json()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        

async def get_func_asyncio(bulk_data, secret):

    print('bulk_data - @@@@@@@@@', bulk_data)
    tasks = []
    # for data in bulk_data:
    #     tasks.append(asyncio.create_task(get_func(data, secret)))
    [tasks.append(asyncio.create_task(get_func(data, secret))) for data in bulk_data]
    results = await asyncio.gather(*tasks)

    return results
        

async def get_func(data, secret):

    commandId = uuid.uuid4()
    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/sale/offer-modification-commands/{commandId}"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {
            'Authorization': f'Bearer {secret}', 
            'Accept': "application/vnd.allegro.public.v1+json",
            'Content-Type': "application/vnd.allegro.public.v1+json",
            }
        product_result = requests.put(url, headers=headers, json=data)
        result = product_result.json()
        print('RESULT - DELIVERY_PRICE STATUS - @@@@@@@@@', product_result.content)
        if product_result.status_code == 201:
            print('RESULT - DELIVERY_PRICE STATUS 201 - @@@@@@@@@')
            print('RESULT - DELIVERY_PRICE - @@@@@@@@@', json.dumps(result, indent=4))
            return result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def DELIVERY_PRICE(request, name, secret, offers):

    if request.user.is_authenticated:
        shipping_rates = all_shipping_rates(request, name, secret)
        # print('RESULT - shipping_rates - @@@@@@@@@', shipping_rates)
        offers_list = [{'id': offer_id} for offer_id in offers.split(',')]

        bulk_data = []

        if request.method == 'POST':
            count = 0
            shippingId = request.POST.get('shipping')
            shipping_time = request.POST.get('shipping_time')

            print('********************** offers_list ****************************', offers_list)
            print('********************** shippingId ****************************', shippingId)
            print('********************** shipping_time ****************************', shipping_time)

            if shippingId is not None:
                shippingId_data = {
                    "modification":
                        {
                            "delivery": {
                                "shippingRates": {
                                "id": shippingId
                                }
                            }
                        },
                    "offerCriteria":[
                        {
                            "type":"CONTAINS_OFFERS",
                            "offers": offers_list,
                        }
                    ]
                }
                bulk_data.append(shippingId_data)
                
            if shipping_time is not None: 
                shipping_time_data = {
                    "modification":
                        {
                            "delivery": {
                            "handlingTime": shipping_time, 
                            }
                        },
                    "offerCriteria":[
                        {
                            "type":"CONTAINS_OFFERS",
                            "offers": offers_list,
                        }
                    ]
                }
                bulk_data.append(shipping_time_data)
            
            if bulk_data:
                result = asyncio.run(get_func_asyncio(bulk_data, secret))
                if result:
                    context = {
                        'result': result,
                        'name': name,
                        'offers_list': offers_list,
                    }
                    return redirect('get_all_offers', name=name)
                # print('############### bulk_data #################', bulk_data)
        context = {
                    'shipping_rates': shipping_rates,
                    'name': name,
                }

        return render(request, 'bulk_shipping_rates.html', context)
    

def DELIVERY_TIME (request, name, secret, offers):

    if request.user.is_authenticated:
        shipping_rates = all_shipping_rates(request, name, secret)
        print('RESULT - shipping_rates - @@@@@@@@@', shipping_rates)

        # # secret = Secret.objects.get(account__name=name)
        commandId = uuid.uuid4()
        offers_list = [{'id': offer_id} for offer_id in offers.split(',')]

        if request.method == 'POST':
            shipping_time = request.POST.get('shipping_time')

            print('********************** offers_list ****************************', offers_list)
            print('********************** shipping_time ****************************', shipping_time)

            data = {
                    "modification":
                        {
                            "delivery": {
                            "handlingTime": shipping_time, 
                            }
                        },
                    "offerCriteria":[
                        {
                            "type":"CONTAINS_OFFERS",
                            "offers": offers_list,
                        }
                    ]
                }


            try:
                url = f"https://api.allegro.pl.allegrosandbox.pl/sale/offer-modification-commands/{commandId}"
                # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
                headers = {
                    'Authorization': f'Bearer {secret}', 
                    'Accept': "application/vnd.allegro.public.v1+json",
                    'Content-Type': "application/vnd.allegro.public.v1+json",
                    }
                product_result = requests.put(url, headers=headers, json=data)
                result = product_result.json()
                print('RESULT - DELIVERY_PRICE STATUS - @@@@@@@@@', product_result)
                if product_result.status_code == 201:
                    print('RESULT - DELIVERY_PRICE STATUS 201 - @@@@@@@@@')
                    print('RESULT - DELIVERY_PRICE - @@@@@@@@@', json.dumps(result, indent=4))
                    context = {
                        'result': product_result.json(),
                        'name': name,
                        'offers_list': offers_list,
                    }
                    return redirect('get_all_offers', name=name)
            except requests.exceptions.HTTPError as err:
                raise SystemExit(err)
        context = {
                    'shipping_rates': shipping_rates,
                    'name': name,
                }

        return render(request, 'bulk_delivery_time.html', context)


def JSON_OFFERS(request):

    if request.user.is_authenticated:
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name')
        ids = data.get('ids')
        secret = Secret.objects.get(account__name=name)
        print(' ******************* JSON_OFFERS offers ******************* ', ids)

        result = asyncio.run(download_all_offers(request, ids, secret.access_token))
        buffer = io.BytesIO()
        json_string = json.dumps(result, indent=4, ensure_ascii=False) # ensure_ascii=False for polish symbols
        buffer.write(json_string.encode('utf-8'))
        buffer.seek(0)

        # Serve the file as a downloadable response
        response = HttpResponse(buffer, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{name}_offers.json"'
        return response
    else:
        return HttpResponse(status=401, content='User not authenticated')
        