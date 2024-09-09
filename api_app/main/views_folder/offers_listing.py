import json
from ..api_service import sync_service
from django.http import HttpResponse
from django.shortcuts import render


def offers_listing(request, name):

    url = 'offers/listing/?category.id=11763&sort=-price&limit=60&offset=0'
    debug_name = 'offers_listing 4'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)
    print(' @*@*@*@*@*@*@*@*@*@*@*@*@ offers_listing 11 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))
    categories = get_all_categories(request, name)
    
    context = {
        'result': result,
        'categories': categories,
    }

    return render(request, 'listing/offers_listing.html', context)


def get_all_categories(request, name):

    url = 'sale/categories' 
    debug_name = 'get_all_categories 23'
    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)
    print(' @*@*@*@*@*@*@*@*@*@*@*@*@ get_all_categories 23 @*@*@*@*@*@*@*@*@*@*@*@*@ ', json.dumps(result, indent=4))

    return result
