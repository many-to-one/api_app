from django.shortcuts import render, redirect, get_object_or_404
from ..models import Secret
import requests
import asyncio
from ..utils import get_next_token
import httpx
from django.http import HttpResponse

def get_all_offers_api(request, name):

    if request.user.is_authenticated:

        # print('******* name ********', name)
        secret = Secret.objects.get(account__name=name)
        # print('******* secret ********', secret)
        # print('******* secret.access_token ********', secret.access_token)

        try:
            url = "https://api.allegro.pl.allegrosandbox.pl/sale/offers"
            # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            product_result = requests.get(url, headers=headers, verify=True)
            result = product_result.json()
            # for of in result['offers']:
                # print('******* get_all_offers ********', of)
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, name)
                        # Retry fetching orders with the new token
                        return get_all_offers_api(request, name)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': name}
                        return render(request, 'invalid_token.html', context)
            # print(" ############### shipping_rates ################## ", shipping_rates)
            print(" ############### product_result.json() API ################## ", product_result.json())

            return product_result.json(),
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    else:
        return redirect('login_user')
    

def post_set_api(request, name, offers, main_offer_id):

    if request.user.is_authenticated:

        tasks = []

        secret = Secret.objects.get(account__name=name)
        # print('******* secret ********', secret)
        # print('******* secret.access_token ********', secret.access_token)

        offer_criteria_offers = []
        for offer in offers:
            offer_criteria_offers.append({
                "id": f'{offer}',
                "quantity": 1, #offer['quantity'],
                "promotionEntryPoint": False, #offer['promotionEntryPoint']
            })

        res = asyncio.run(prepare_offers(request, name, secret, main_offer_id, offer_criteria_offers))

        # print('############ post_set_api res ##############', res)
        # res = prepare_offers(request, name, secret, main_offer_id, offers)
        return res
       
    else:
        return redirect('login_user')
    

async def prepare_offers(request, name, secret, main_offer_id, offers):

    res = await contain_offers(request, name, secret, main_offer_id, offers)

    print('############ prepare_offers res ##############', res)
    return res  


async def contain_offers(request, name, secret, main_offer_id, offers):

    # print('############ contain_offers ##############', offer)
    main_offer = {
        "id": f'{main_offer_id}',
        "quantity": 1, 
        "promotionEntryPoint": True, 
    }
    offers.insert(0, main_offer)
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.allegro.pl.allegrosandbox.pl/sale/loyalty/promotions" 
            # headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            headers = {
                'Authorization': f'Bearer {secret.access_token}',
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Content-Type': 'application/vnd.allegro.public.v1+json'
            }
            data = {
                "benefits": [
                    {
                    "specification": {
                        "type": "ORDER_FIXED_DISCOUNT",
                        # "thresholds": [
                        # {
                        #     "discount": {
                        #     "percentage": "0.1"
                        #     }
                        # },
                        # ]
                        "value": {                         
                                                
                            "amount": "0",
                            "currency": "PLN"
                        }
                    }
                    }
                ],
                "offerCriteria": [
                    {
                    "type": "CONTAINS_OFFERS",
                    "offers": offers,
                    }
                ]
                }
            product_result = await client.post(url, headers=headers, json=data)
            result = product_result.json()
            # for of in result['offers']:
                # print('******* get_all_offers ********', of)
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, name)
                        # Retry fetching orders with the new token
                        return get_all_offers_api(request, name)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': name}
                        return render(request, 'invalid_token.html', context)
            # print(" ############### shipping_rates ################## ", shipping_rates)
            print(" ############### post_set_api ################## ", result)
            response = HttpResponse("Cookie Set")
            response.set_cookie('set_offers_response', 'test')

            # return product_result.json(), 
            return result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    




    ################################################################################################################################


def post_set_api_one(request, name, offers, main_offer_id):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)
        # print('******* secret ********', secret)
        # print('******* secret.access_token ********', secret.access_token)

        res = asyncio.run(prepare_offers_one(request, name, secret, main_offer_id, offers))

        # print('############ post_set_api res ##############', res)
        # res = prepare_offers(request, name, secret, main_offer_id, offers)
        return res
        
    else:
        return redirect('login_user')
    

async def prepare_offers_one(request, name, secret, main_offer_id, offers):

    # print('############ prepare_offers ##############', offers)

    tasks = []

    for offer in offers:
        task = asyncio.create_task(contain_offers_one(request, name, secret, main_offer_id, offer))
        tasks.append(task)

    # Gathering results from all tasks
    res = await asyncio.gather(*tasks)

    print('############ prepare_offers res ##############', res)
    return res  


async def contain_offers_one(request, name, secret, main_offer_id, offer):

    # print('############ contain_offers ##############', offer)
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.allegro.pl.allegrosandbox.pl/sale/loyalty/promotions" 
            # headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            headers = {
                'Authorization': f'Bearer {secret.access_token}',
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Content-Type': 'application/vnd.allegro.public.v1+json'
            }
            data = {
                "benefits": [
                    {
                    "specification": {
                        "type": "ORDER_FIXED_DISCOUNT",
                        # "thresholds": [
                        # {
                        #     "discount": {
                        #     "percentage": "0.1"
                        #     }
                        # },
                        # ]
                        "value": {                         
                                                
                            "amount": "0",
                            "currency": "PLN"
                        }
                    }
                    }
                ],
                "offerCriteria": [
                    {
                    "type": "CONTAINS_OFFERS",
                    "offers": [
                        {
                            "id": f'{main_offer_id}',
                            "quantity": 1, #offer['quantity'],
                            "promotionEntryPoint": True, #offer['promotionEntryPoint']
                        },
                        {
                            "id": f'{offer}',
                            "quantity": 1, #offer['quantity'],
                            "promotionEntryPoint": False, #offer['promotionEntryPoint']
                        },
                    ],
                    }
                ]
                }
            product_result = await client.post(url, headers=headers, json=data)
            result = product_result.json()
            # for of in result['offers']:
                # print('******* get_all_offers ********', of)
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, name)
                        # Retry fetching orders with the new token
                        return get_all_offers_api(request, name)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': name}
                        return render(request, 'invalid_token.html', context)
            # print(" ############### shipping_rates ################## ", shipping_rates)
            print(" ############### post_set_api ################## ", result)
            response = HttpResponse("Cookie Set")
            response.set_cookie('set_offers_response', 'test')

            # return product_result.json(), 
            return result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

################################################################################################################################


def get_all_sets_api(request, name):

    if request.user.is_authenticated:

        # print('******* name ********', name)
        secret = Secret.objects.get(account__name=name)
        # print('******* secret ********', secret)
        # print('******* secret.access_token ********', secret.access_token)

        try:
            url = "https://api.allegro.pl.allegrosandbox.pl/sale/loyalty/promotions?promotionType=BUNDLE"
            # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            product_result = requests.get(url, headers=headers, verify=True)
            result = product_result.json()
            # for of in result['offers']:
                # print('******* get_all_offers ********', of)
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, name)
                        # Retry fetching orders with the new token
                        return get_all_offers_api(request, name)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': name}
                        return render(request, 'invalid_token.html', context)
            # print(" ############### shipping_rates ################## ", shipping_rates)
            # print(" ############### get_all_sets ################## ", product_result.json())

            return product_result.json(),
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    else:
        return redirect('login_user')
    


async def get_image_api(request, name, secret, offers):

    if request.user.is_authenticated:

        # print("############### get_image_api ##################", offers)
        tasks = []

        for offer in offers:
            task = asyncio.create_task(get_image(request, name, secret, offer))
            tasks.append(task)

        res = await asyncio.gather(*tasks)

        return res
    

async def get_image(request, name, secret, offer):

    print('offer RESULT @@@@@@@@@', offer['id'])
    id = offer['id']

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        # Allegro doesn't accept httpx in this case(maybe to fast for api call)
        product_result = requests.get(url, headers=headers, verify=True) 
        await asyncio.sleep(1)
        result = product_result.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token)
                    # Retry fetching orders with the new token
                    return await get_image(request, name, secret, offer)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')
        print('@@@@@@@@@ RESULT get_image productSet @@@@@@@@@', result)
        return result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


# async def get_image(request, name, secret, offer):

#     print('offer RESULT @@@@@@@@@', offer['id'])
#     id = offer['id']

#     try:
#         async with httpx.AsyncClient() as client:
#             url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
#             # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
#             headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
#             # Allegro doesn't accept httpx in this case(maybe to fast for api call)
#             product_result = await client.get(url, headers=headers) 
#             result = product_result.json()
#             if 'error' in result:
#                 error_code = result['error']
#                 if error_code == 'invalid_token':
#                     # print('ERROR RESULT @@@@@@@@@', error_code)
#                     try:
#                         # Refresh the token
#                         new_token = get_next_token(request, secret.refresh_token)
#                         # Retry fetching orders with the new token
#                         return await get_image(request, name, secret, offer)
#                     except Exception as e:
#                         print('Exception @@@@@@@@@', e)
#                         return redirect('invalid_token')
#             print('@@@@@@@@@ RESULT get_image productSet @@@@@@@@@', result)
#             return result
#     except requests.exceptions.HTTPError as err:
#         raise SystemExit(err)


