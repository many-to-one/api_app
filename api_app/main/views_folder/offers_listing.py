import asyncio
import json
from ..api_service import sync_service, async_service
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import Secret
from datetime import datetime
from django.core import serializers
import logging


def offers_listing(request, name):
    
    secret = Secret.objects.get(account__name=name)
    result = asyncio.run(get_offers(request, secret, name))
    categories = asyncio.run(get_all_categories(request, secret, name))

    # print("^^^^^^^^^^^^^^^^^categories:^^^^^^^^^^^^^^^^^", categories)

    context = {
        'result': result,
        'categories': categories[0]["categories"],
        'sub_categories': categories[1] #json.dumps(sub_categories) # categories[1]
    }

    return render(request, 'listing/offers_listing.html', context)


def optimize_subcategories(sub_categories):
    optimized_sub_categories = []
    # print("Zoptymalizowane dane sub_categories:", sub_categories)
    for sub_cat in sub_categories:
        for cat in sub_cat['categories']:
            optimized_sub_categories.append({
                    'id': cat['id'],
                    'name': cat['name'],
                    'parent': cat['parent']
                })

    # print("Zoptymalizowane dane:", optimized_sub_categories)
    return optimized_sub_categories




async def get_offers(request, secret, name):

    url = 'offers/listing/?category.id=11818&sort=-relevance&fallback=true&parameter.11323=11323_1&limit=60' #&offset=60 319060
    # url = 'offers/listing?sort=-relevance&limit=60'
    debug_name = 'offers_listing 18'
    token = secret.access_token
    refresh_token = secret.refresh_token
    offers = await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)
    time_ = datetime.now().strftime("%H:%M:%S")

    logging.basicConfig(filename='output.log', level=logging.DEBUG)
    logging.debug(json.dumps(offers, indent=4))

    # for offer in

    # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_offers 33 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(offers, indent=4), time_) #json.dumps(offers, indent=4), 

    return offers



async def get_all_categories(request, secret, name):

    url = 'sale/categories' 
    # url2 = 'sale/categories/?parent.id=38d588fd-7e9c-4c42-a4ae-6831775eca45'
    debug_name = 'offers_listing 18'
    token = secret.access_token
    refresh_token = secret.refresh_token
    categories = await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)
    print(' @*@*@*@*@*@*@*@*@*@*@*@*@ categories 48 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(categories, indent=4))

    full_categories = []
    full_categories.append(categories)
    tasks = []
    tasks_1 = []
    for cat in categories['categories']:
        categoryId = cat['id']
        tasks.append(asyncio.create_task(
            get_sub_categories(request, secret, name, categoryId)
        ))
    sub = await asyncio.gather(*tasks)
    full_categories.append(sub)
    # if sub:
    #     for s in sub:
    #         for c in s['categories']:
    #             id = c['id']
    #             tasks_1.append(asyncio.create_task(
    #                 get_sub_categories(request, secret, name, id)
    #             ))
    #     sub_1 = await asyncio.gather(*tasks_1)
    #     # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ sub_1 48 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(sub_1, indent=4))
    #     full_categories.append(sub_1)
    time_ = datetime.now().strftime("%H:%M:%S")

    # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_all_categories 48 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(full_categories[0], indent=4)) #json.dumps(full_categories[1], indent=4), 

    return full_categories


async def get_sub_categories(request, secret, name, categoryId):

    # print('$$$$$$$$$$$$$$$$$$ TYPE $$$$$$$$$$$$$$$$$$$$', type(categoryId))

    # categoryId = '11763'
    url = f'sale/categories/?parent.id={categoryId}' 
    debug_name = 'get_category_param 58'
    token = secret.access_token
    refresh_token = secret.refresh_token
    sub_categories = await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)
    # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_category_param 58 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(sub_categories, indent=4))

    return sub_categories


def offers_listing_response(request):

    data = json.loads(request.body.decode('utf-8'))
    value = data.get('value')
    filter = data.get('filter')
    name = data.get('name')
    path = data.get('path')
    id = '319060' #'319060'
    # url = f'offers/listing/?{filter}={value}&sort=+price&limit=60' #&offset=60 
    url = f'offers/listing/?{path}&limit=60'
    debug_name = 'offers_listing_response 25'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)
    # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ offers_listing_response 25 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))
    print(' @*@*@*@*@*@*@*@*@*@*@*@*@ offers_listing_response url @*@*@*@*@*@*@*@*@*@*@*@*@ ', url)

    return JsonResponse ({
        'result': result,
    })