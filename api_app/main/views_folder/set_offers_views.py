import requests
from django.shortcuts import render, redirect

from .api_results import get_all_offers_api, post_set_api, post_set_api_one, get_all_sets_api
from ..utils import *
from ..models import *

def set_offers(request, name):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)

        all_sets = get_all_sets_api(request, name)
        # for set in all_sets[0]['promotions']:
        #     print(" ############### set ################## ", set)

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

            # for res in result["offers"]:
            #     print(" ############### one res ################## ", res)



            # Iterate through each promotion in all_sets[0]['promotions']
            for set_item in all_sets[0]['promotions']:
                set_id = set_item['id']
                print("############### set ##################", set_id)

                # Now check if this id exists in any of the result["offers"]
                for res_item in result["offers"]:
                    res_id = res_item['id']
                    print("############### one res ##################", res_id)

                    # Check if the id in the promotion matches any id in the offers
                    if set_id == res_id:
                        print(f"Match found! ID {set_id} is present in both.")
                        # You can break the inner loop if you only care about the first match
                        break
                else:
                    print(f"No match found for ID {set_id} in result['offers'].")


            context = {
                'result': result,
                'name': name,
                'sets': all_sets[0]['promotions']
            }
            return render(request, 'set_offers.html', context)
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    else:
        return redirect('login_user')
    

def set_add(request, name, offer_id):
    result = get_all_offers_api(request, name)
    context = {
        'result': result[0],
        'name': name,
        'main_offer_id': offer_id,
    }
    return render(request, 'set_add.html', context)


def add_offers(request):

    data = json.loads(request.body.decode('utf-8'))
    offers = data.get('offers')
    name = data.get('name') 
    main_offer_id = data.get('main_offer_id')
    print(' ######### offers ##########', offers)
    res = post_set_api(request, name, offers, main_offer_id)
    print(' ######### res ##########', res)
    if 'errors' in res:
        print(' ######### res errors ##########', res['errors'][0]['userMessage'])
        if any('id' in item for item in res):
            print(' ######### res id in res[0] ##########', res)
            context = {
                'result': res,
                'name': name,
                'message': 'Stworzyłeś zestaw(y) offert, ale w zestawach podobny(e) już isnieje(ą)',
                'status': '!ok',
            }
        else:
            context = {
                'result': res[0]['errors'][0]['userMessage'],
                'name': name,
                'message': res[0]['errors'][0]['userMessage'], 
                'status': 'error'
            }
    else:
        context = {
            'result': res,
            'name': name,
            'message': 'Stworzyłeś zestaw(y) offert',
            'status': 'ok',
        }
    
    return JsonResponse(
                {
                    'message': 'Stock updated successfully',
                    'context': context,
                }, 
                status=200,
            )
    


def add_offers_one(request):

    data = json.loads(request.body.decode('utf-8'))
    offers = data.get('offers')
    name = data.get('name') 
    main_offer_id = data.get('main_offer_id')
    print(' ######### offers ##########', offers)
    res = post_set_api_one(request, name, offers, main_offer_id)
    print(' ######### res ##########', res)
    if 'errors' in res:
        print(' ######### res errors ##########', res['errors'][0]['userMessage'])
        if any('id' in item for item in res):
            print(' ######### res id in res[0] ##########', res)
            context = {
                'result': res,
                'name': name,
                'message': 'Stworzyłeś zestaw(y) offert, ale w zestawach podobny(e) już isnieje(ą)',
                'status': '!ok',
            }
        else:
            context = {
                'result': res[0]['errors'][0]['userMessage'],
                'name': name,
                'message': res[0]['errors'][0]['userMessage'], 
                'status': 'error'
            }
    else:
        context = {
            'result': res,
            'name': name,
            'message': 'Stworzyłeś zestaw(y) offert',
            'status': 'ok',
        }
    
    return JsonResponse(
                {
                    'message': 'Stock updated successfully',
                    'context': context,
                }, 
                status=200,
            )
