import requests
from django.shortcuts import render, redirect

from .api_results import get_all_offers_api, post_set_api
from ..utils import *
from ..models import *

def set_offers(request, name):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)

        try:
            url = "https://api.allegro.pl.allegrosandbox.pl/sale/offers"
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
                        return set_offers(request, name)
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
    

def set_add(request, name):
    result = get_all_offers_api(request, name)
    context = {
        'result': result[0],
        'name': name,
    }
    return render(request, 'set_add.html', context)


def add_offers(request):

    data = json.loads(request.body.decode('utf-8'))
    offers = data.get('offers')
    name = data.get('name')
    print(' ######### offers ##########', offers)
    res = post_set_api(request, name, offers)
    context = {
        'result': res,
        'name': name,
    }
    
    return JsonResponse(
                {
                    'message': 'Stock updated successfully',
                    'context': context,
                }, 
                status=200,
            )
    
