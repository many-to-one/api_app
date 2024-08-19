import requests
from django.shortcuts import render, redirect

from main.views_folder.offer_views import get_one_offer, return_async_offer

from .api_results import edit_set, get_all_offers_api, get_image, get_image_api, get_offer_by_id, get_set, post_set_api, post_set_api_one, get_all_sets_api, prepare_offer_by_id
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
            # print("############### set_offers *** ##################", result)

            all_sets = get_all_sets_api(request, name)
            print("############### all_sets ++ ##################", all_sets)
            offers = []
            for set_item in all_sets[0]['promotions']:
                offer = set_item['offerCriteria'][0]['offers']
                discount = set_item['benefits'][0]['specification']['value']['amount']
                # print("############### offer ++ ##################", offer)
                sum_ = 0
                for f in offer:
                    for of in result['offers']:
                        if of['id'] == f['id']:
                            # print("############### of ++ ##################", of['sellingMode']['price']['amount'])
                            sum_ += float(of['sellingMode']['price']['amount'])
                    # print("############### sum_ ##################", sum_  )
                price_after = sum_ - float(discount)
                discount_percentage = (float(discount) / sum_) * 100
                offers.append(
                        [
                            {'set_id': set_item['id']}, 
                            offer, 
                            {'price': "{:.2f}".format(float(sum_))}, 
                            {'discount': "{:.2f}".format(float(discount))}, 
                            {'price_after': "{:.2f}".format(float(price_after))},
                            {'discount_percentage': "{:.2f}".format(float(discount_percentage))}
                        ]
                    )

            print("############### offers ##################", offers  )

            context = {
                'result': result,
                'name': name,
                'sets': offers, #all_sets[0]['promotions'],
            }

            return render(request, 'set_offers_test.html', context)
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
    if 'errors' in res[0]:
        print(' ######### res errors ##########', res[0]['errors'][0]['userMessage'])
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

def add_discount(request, name):

    secret = Secret.objects.get(account__name=name)

    if request.method == 'POST':
        data = json.loads(request.body)
        set_id = data['set_id']
        disc__money = data['disc__money']
        disc__percent = data['disc__percent']
        disc__piece = data['disc__piece']
        disc__price = data['disc__price']

        res = get_set(request, name, secret, set_id)
        res['benefits'][0]['specification']['value']['amount'] = disc__money
        filtered_dict = {key: value for key, value in res.items() if key not in ['id', 'createdAt', 'status']}
        edit = edit_set(request, secret, name, filtered_dict, set_id)
        print('************ disc__percent *************', disc__percent, disc__price)
        # print('************ add_discount *************', set_id, disc__money, disc__percent, disc__piece)

        return JsonResponse(
                {
                    'message': 'Discount updated successfully',
                    'userMessage': 'Rabat dodany poprawnie',
                    'res': edit,
                }, 
                status=200,
            )