import csv
import io
import json, requests
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from ..utils import *
from ..models import *

def set_offers(request, name):

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
                        return get_all_offers(request, name)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': name}
                        return render(request, 'invalid_token.html', context)
            # print(" ############### shipping_rates ################## ", shipping_rates)
            # print(" ############### aftersale_services ################## ", aftersale_services)
            context = {
                'result': product_result.json(),
                'name': name,
            }
            return render(request, 'set_offers.html', context)
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    else:
        return redirect('login_user')