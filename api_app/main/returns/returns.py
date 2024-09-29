import json, requests
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from ..utils import *
from ..models import *
from ..api_service import sync_service


def get_returns(request, name):
    
    url = 'order/customer-returns'
    debug_name = 'get_returns 8'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)

    print(' @@@@@@@@@ - get_returns - @@@@@@@@@ ', json.dumps(result, indent=4))

    offers = get_all_offers(request, name)
    print(' @@@@@@@@@ - offers - @@@@@@@@@ ', json.dumps(offers, indent=4))

    for offer in offers['offers']:
        print(' @@@@@@@@@ - one offer - @@@@@@@@@ ', offer['primaryImage'])

    context = {
        'result': result,  
        'name': name,
        # 'shipping_rates': shipping_rates,
        # 'aftersale_services': aftersale_services,
    }

    return render(request, 'returns/returns.html', context)


# GET ALL OFFERS
def get_all_offers(request, name):
    
    url = 'sale/offers'
    debug_name = 'get_all_offers 126'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)

    # print(' @@@@@@@@@ - get_all_offers - @@@@@@@@@ ', json.dumps(result, indent=4))

    return result