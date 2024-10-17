import requests
from django.shortcuts import render, redirect

from main.offers.offer_views import get_one_offer, return_async_offer

from ..views_folder.api_results import edit_set, get_all_offers_api, get_image, get_image_api, get_offer_by_id, get_set, post_copy_offers, post_copy_offers_api, post_set_api, post_set_api_one, get_all_sets_api, prepare_offer_by_id, prepare_post_copy_offers
from ..utils import *
from ..models import *

from ..api_service import async_service, sync_service

def set_offers(request, name):

    url = f'sale/offers'
    debug_name = 'set_offers (all_offers) 15'
    all_offers = sync_service.Offers(name)
    result = all_offers.get_(request, url, debug_name)
    # print("############### all_offers ##################", result)

    url = f'sale/bundles'
    debug_name = 'set_offers (bundles) 20'
    sets = sync_service.Offers(name)
    all_sets = sets.get_(request, url, debug_name)

    # all_sets = get_all_sets_api(request, name)
    print("############### all_sets ##################", all_sets)

    offers = []
    for set_item in all_sets['bundles']: #[0]['promotions']:
        offer = set_item['offers'] #['offerCriteria'][0]['offers']
        # discount = set_item['discounts'][0]['amount'] #['benefits'][0]['specification']['value']['amount']
        discount = 0
        if 'discounts' in set_item and len(set_item['discounts']) > 0:
            discount = set_item['discounts'][0]['amount']
        sum_ = 0
        for f in offer:
            for of in result['offers']:
                if of['id'] == f['id']:
                    # print("############### of ++ ##################", of['sellingMode']['price']['amount'])
                    sum_ += float(of['sellingMode']['price']['amount']) * f['requiredQuantity']
                    # print("############### offer price * quantity ++ ##################", float(of['sellingMode']['price']['amount']) * f['quantity'])
                    # quantity
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
        'sets': offers[::-1], #all_sets[0]['promotions'],
    }

    return render(request, 'set_offers_test.html', context)

        # try:
        #     url = "https://api.allegro.pl.allegrosandbox.pl/sale/offers" 
        #     headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        #     product_result = requests.get(url, headers=headers, verify=True)
        #     result = product_result.json()
        #     if 'error' in result:
        #         error_code = result['error']
        #         if error_code == 'invalid_token':
        #             # print('ERROR RESULT @@@@@@@@@', error_code)
        #             try:
        #                 # Refresh the token
        #                 new_token = get_next_token(request, secret.refresh_token, name)
        #                 # Retry fetching orders with the new token
        #                 return set_offers(request, name)
        #             except Exception as e:
        #                 print('Exception @@@@@@@@@', e)
        #                 context = {'name': name}
        #                 return render(request, 'invalid_token.html', context)
        #     # print("############### set_offers *** ##################", result)

        #     all_sets = get_all_sets_api(request, name)
        #     print("############### all_sets ++ ##################", all_sets)
            # offers = []
            # for set_item in all_sets[0]['promotions']:
            #     offer = set_item['offerCriteria'][0]['offers']
            #     discount = set_item['benefits'][0]['specification']['value']['amount']
            #     sum_ = 0
            #     for f in offer:
            #         for of in result['offers']:
            #             if of['id'] == f['id']:
            #                 # print("############### of ++ ##################", of['sellingMode']['price']['amount'])
            #                 sum_ += float(of['sellingMode']['price']['amount']) * f['quantity']
            #                 # print("############### offer price * quantity ++ ##################", float(of['sellingMode']['price']['amount']) * f['quantity'])
            #                 # quantity
            #         # print("############### sum_ ##################", sum_  )
            #     price_after = sum_ - float(discount)
            #     discount_percentage = (float(discount) / sum_) * 100
            #     offers.append(
            #             [
            #                 {'set_id': set_item['id']}, 
            #                 offer, 
            #                 {'price': "{:.2f}".format(float(sum_))}, 
            #                 {'discount': "{:.2f}".format(float(discount))}, 
            #                 {'price_after': "{:.2f}".format(float(price_after))},
            #                 {'discount_percentage': "{:.2f}".format(float(discount_percentage))}
            #             ]
            #         )

            # print("############### offers ##################", offers  )

            # context = {
            #     'result': result,
            #     'name': name,
            #     'sets': offers[::-1], #all_sets[0]['promotions'],
            # }

            # return render(request, 'set_offers_test.html', context)
    #     except requests.exceptions.HTTPError as err:
    #         raise SystemExit(err)

    # else:
    #     return redirect('login_user')


    

def set_add(request, name, offer_id):
    result = get_all_offers_api(request, name)
    context = {
        'result': result[0],
        'name': name,
        'main_offer_id': offer_id,
    }
    return render(request, 'set_add.html', context)


def sets_add(request, name, offer_id):
    result = get_all_offers_api(request, name)
    context = {
        'result': result[0],
        'name': name,
        'main_offer_id': offer_id,
    }
    return render(request, 'sets_add.html', context)


def add_offers(request):

    data = json.loads(request.body.decode('utf-8'))
    offers = data.get('offers')
    main_count_data = data.get('main_count')
    print(' ######### main_count ##########', main_count_data)
    main_count = main_count_data[0]
    name = data.get('name') 
    main_offer_id = data.get('main_offer_id')
    print(' ######### main_count ##########', main_count)
    print(' ######### offers ##########', offers)
    res = post_set_api(request, name, main_count, offers, main_offer_id)
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
                'result': res['errors'][0]['userMessage'],
                'name': name,
                'message': res['errors'][0]['userMessage'], 
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
    main_offers = data.get('main_offers')
    offers = data.get('offers')
    name = data.get('name') 
    main_offer_id = data.get('main_offer_id')
    print(' ######### main_offers ##########', main_offers)
    print(' ######### offers ##########', offers)
    res = post_set_api_one(request, name, main_offers, offers, main_offer_id)
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
        # disc__piece = data['disc__piece']
        count_array = data['count_array']
        disc__price = data['disc__price']

        res = get_set(request, name, secret, set_id)
        for offer in count_array:
            for k, v in offer.items():
                print('**** k ****', k)
                print('**** v ****', v)
                for item in res['offerCriteria'][0]['offers']:
                    print('**** item ****', item['id'])
                    if item['id'] == str(k):
                        item['quantity'] = v
        res['benefits'][0]['specification']['value']['amount'] = disc__money
        filtered_dict = {key: value for key, value in res.items() if key not in ['id', 'createdAt', 'status']}
        edit = edit_set(request, secret, name, filtered_dict, set_id)
        print('************ disc__percent *************', disc__percent, disc__price, count_array)
        # print('************ add_discount *************', set_id, disc__money, disc__percent, disc__piece)

        return JsonResponse(
                {
                    'message': 'Discount updated successfully',
                    'userMessage': 'Rabat dodany poprawnie',
                    'res': edit,
                }, 
                status=200,
            )
    

def add_copy_offers_one(request):

    if request.user.is_authenticated:

        data = json.loads(request.body.decode('utf-8'))
        print('********** add_copy_offers_one *************', data)
        name = data['name']
        offers = data['count_array']
        amount = data['disc__money']
        # amount = float(amount_)
        print(' ######### amount ##########', amount)
        print(' ######### type amount ##########', type(amount))
        main_offer = data['main_offer']
        # for offer in offers:
        #     print(' ######### res ##########', offer)
        secret = Secret.objects.get(account__name=name)
        res = post_copy_offers_api(request, secret, offers, amount, main_offer)
        print(' ######### secret ##########', secret)

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
    


def delete_set(request, name, id):

    print("############### delete_set id, name ##################", id, name)

    url = f'sale/bundles/{id}'
    debug_name = 'set_offers (all_offers) 15'
    all_sets = sync_service.Offers(name)
    result = all_sets.delete_(request, url, debug_name)
    # result = all_offers.de(request, url, debug_name)
    print("############### delete_set ##################", result)

    # if 'errors' in result[0]:
    #     context = {
    #                 'result': result[0]['errors'][0]['userMessage'],
    #                 'name': name,
    #                 'message': result[0]['errors'][0]['userMessage'], 
    #                 'status': 'error'
    #             }
    # else:
    context = {
                'result': result,
                'name': name,
                'message': 'Zestaw(y) usunięto poprawnie',
                'status': 'ok',
            }

    return JsonResponse(
                    {
                        'message': 'Set(s) deleted successfully',
                        'context': context,
                    }, 
                    status=200,
                )