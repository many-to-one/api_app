import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from ..utils import *
import requests


def get_all_offers(request):

    user = get_user(request)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/sale/offers"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {user.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        print('RESULT - get_all_offers - @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json()
        }
        return render(request, 'get_all_offers.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)