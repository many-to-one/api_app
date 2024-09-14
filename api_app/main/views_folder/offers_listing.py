import json
from ..api_service import sync_service
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def offers_listing(request, name):

    url = 'offers/listing/?category.id=11818&sort=+price&limit=60' #&offset=60
    debug_name = 'offers_listing 4'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)
    print(' @*@*@*@*@*@*@*@*@*@*@*@*@ offers_listing 11 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))
    categories = get_all_categories(request, name)
    
    context = {
        'result': result,
        'categories': categories["categories"],
    }

    return render(request, 'listing/offers_listing.html', context)


def offers_listing_response(request):

    data = json.loads(request.body.decode('utf-8'))
    value = data.get('value')
    filter = data.get('filter')
    name = data.get('name')
    url = f'offers/listing/?{filter}={value}&sort=+price&limit=60' #&offset=60
    debug_name = 'offers_listing_response 25'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)
    print(' @*@*@*@*@*@*@*@*@*@*@*@*@ offers_listing_response 25 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))

    return JsonResponse ({
        'result': result,
    })


def get_all_categories(request, name):

    url = 'sale/categories' 
    debug_name = 'get_all_categories 23'
    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)
    # print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_all_categories 23 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))

    return result

