from django.shortcuts import render, redirect, get_object_or_404
from ..models import Secret
import requests

from ..utils import get_next_token


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
            # print(" ############### product_result.json() API ################## ", product_result.json())

            return product_result.json(),
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    else:
        return redirect('login_user')
    

def post_set_api(request, name, offers):

    if request.user.is_authenticated:

        offer_criteria_offers = []
        for offer in offers:
            offer_criteria_offers.append({
                "id": offer,
                "quantity": 1, #offer['quantity'],
                "promotionEntryPoint": True, #offer['promotionEntryPoint']
            })

        # print('******* name ********', name)
        secret = Secret.objects.get(account__name=name)
        # print('******* secret ********', secret)
        # print('******* secret.access_token ********', secret.access_token)

        try:
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
                            "id": '7774746246',
                            "quantity": 1, #offer['quantity'],
                            "promotionEntryPoint": True, #offer['promotionEntryPoint']
                        },
                        {
                            "id": '7774746244',
                            "quantity": 1, #offer['quantity'],
                            "promotionEntryPoint": False, #offer['promotionEntryPoint']
                        }
                    ],
                    }
                ]
                }
            product_result = requests.post(url, headers=headers, json=data)
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

            return product_result.json(),
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    else:
        return redirect('login_user')