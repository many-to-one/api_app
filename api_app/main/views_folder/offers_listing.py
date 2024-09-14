import asyncio
import json
from ..api_service import sync_service, async_service
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import Secret
from datetime import datetime


def offers_listing(request, name):
    
    secret = Secret.objects.get(account__name=name)
    result = asyncio.run(get_offers(request, secret, name))
    categories = asyncio.run(get_all_categories(request, secret, name))

    context = {
        'result': result,
        'categories': categories[0]["categories"],
        'sub_categories': categories[1]["categories"]
    }

    # for cat in categories[0]["categories"]:
    #     for sub in categories[1]["categories"]:
    #         if cat['id'] == sub['parent']['id']:
    #             print(' @*@*@*@*@*@*@*@*@*@*@*@*@ cat.id @*@*@*@*@*@*@*@*@*@*@*@*@ ', sub)

    # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ offers_listing 10 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(categories[1]["categories"], indent=4))

    return render(request, 'listing/offers_listing.html', context)



async def get_offers(request, secret, name):

    url = 'offers/listing/?category.id=319060&sort=+price&limit=60' #&offset=60
    # url = 'offers/listing?sort=-relevance&limit=60'
    debug_name = 'offers_listing 18'
    token = secret.access_token
    refresh_token = secret.refresh_token
    offers = await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)
    time_ = datetime.now().strftime("%H:%M:%S")

    print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_offers 33 @*@*@*@*@*@*@*@*@*@*@*@*@ ', time_) #json.dumps(offers, indent=4), 

    return offers


async def get_all_categories(request, secret, name):

    url = 'sale/categories' 
    debug_name = 'offers_listing 18'
    token = secret.access_token
    refresh_token = secret.refresh_token
    categories = await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)

    full_categories = []
    full_categories.append(categories)
    tasks = []
    for cat in categories['categories']:
        categoryId = cat['id']
        tasks.append(asyncio.create_task(
            get_sub_categories(request, secret, name, categoryId)
        ))
    sub = await asyncio.gather(*tasks)
    full_categories.append(sub[0])
    time_ = datetime.now().strftime("%H:%M:%S")

    print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_all_categories 48 @*@*@*@*@*@*@*@*@*@*@*@*@ ', time_) #json.dumps(full_categories[1], indent=4), 

    return full_categories


async def get_sub_categories(request, secret, name, categoryId):

    # categoryId = '11763'
    url = f'sale/categories/?parent.id={categoryId}' 
    debug_name = 'get_category_param 58'
    token = secret.access_token
    refresh_token = secret.refresh_token
    sub_categories = await async_service.async_get(request, name=name, url=url, token=token, refresh_token=refresh_token, debug_name=debug_name)
    # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_category_param 58 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(sub_categories, indent=4))

    return sub_categories


# async def get_category_param(request, name):

#     categoryId = '11763'
#     url = f'sale/categories/?parent.id={categoryId}' 
#     debug_name = 'get_all_categories 23'
#     offers = sync_service.Offers(name)
#     result = offers.get_(request, url, debug_name)
#     print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_category_param 58 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))

#     return result



# def offers_listing(request, name):

#     url = 'offers/listing/?category.id=319060&sort=+price&limit=60' #&offset=60
#     # url = 'offers/listing?sort=-relevance&limit=60'
#     debug_name = 'offers_listing 7'

#     offers = sync_service.Offers(name)
#     result = offers.get_(request, url, debug_name)
#     print(' @*@*@*@*@*@*@*@*@*@*@*@*@ offers_listing 11 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))
#     categories = get_all_categories(request, name)
    
#     context = {
#         'result': result,
#         'categories': categories["categories"],
#     }

#     return render(request, 'listing/offers_listing.html', context)


def offers_listing_response(request):

    data = json.loads(request.body.decode('utf-8'))
    value = data.get('value')
    filter = data.get('filter')
    name = data.get('name')
    id = '319060' #'319060'
    # url = f'offers/listing/?{filter}={value}&sort=+price&limit=60' #&offset=60 
    url = f'offers/listing/?{filter}={value}&sort=+price&limit=60'
    debug_name = 'offers_listing_response 25'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)
    # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ offers_listing_response 25 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))
    # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ offers_listing_response url @*@*@*@*@*@*@*@*@*@*@*@*@ ', url)

    return JsonResponse ({
        'result': result,
    })


# def get_all_categories(request, name):

#     url = 'sale/categories' 
#     debug_name = 'get_all_categories 23'
#     offers = sync_service.Offers(name)
#     result = offers.get_(request, url, debug_name)
#     print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_all_categories 23 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))
#     get_category_param(request, name)

#     return result


# def get_category_param(request, name):

#     categoryId = '11763'
#     url = f'sale/categories/?parent.id={categoryId}' 
#     debug_name = 'get_all_categories 23'
#     offers = sync_service.Offers(name)
#     result = offers.get_(request, url, debug_name)
#     print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_category_param 58 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))

#     return result

