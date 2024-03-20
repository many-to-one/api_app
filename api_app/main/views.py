import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .utils import *
import requests
import os
from dotenv import load_dotenv
load_dotenv()

REDIRECT_URI = os.getenv('REDIRECT_URI')      # wprowadź redirect_uri
AUTH_URL = os.getenv('AUTH_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

def index(request):
    if request.user.is_authenticated:
        return render(request, 'index.html')
    else:
        return render(request, 'login.html')
    
def get_code(request):
    return render(request, 'get_code.html')

def get_authorization_code(request):

    REDIRECT_URI_ =' http://localhost:8000/get_code'   

    user = get_user(request)

    authorization_redirect_url = AUTH_URL + '?response_type=code&client_id=' + user.CLIENT_ID + \
                                 '&redirect_uri=' + REDIRECT_URI_
    # print("Zaloguj do Allegro - skorzystaj z url w swojej przeglądarce oraz wprowadź authorization code ze zwróconego url: ")
    # print("---  " + authorization_redirect_url + "  ---")

    return redirect(authorization_redirect_url)
        
    
def get_access_token(request, authorization_code):
 
    user = get_user(request)
    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': 'http://localhost:8000/get_code'}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(user.CLIENT_ID, user.CLIENT_SECRET))
        print("RESPONSE CONTENT:", access_token_response.status_code)
        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        if access_token:
            user.access_token = access_token
            user.save()
            print(f'@#@#@#@# tokens #@#@#@# --------- {tokens}')
            return JsonResponse({
                   'message': tokens,
               })
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

#################################################################################################################################################
############################################################################ POST NEW PRODUCT ###################################################
#################################################################################################################################################

def post_product(request):

    user = get_user(request)
    
    url = f'https://api.allegro.pl.allegrosandbox.pl/sale/product-offers'

    headers = {
        'Authorization': f'Bearer {user.access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }


    
    data = {
    'productSet': [{
        'product': {
            'category': {
                'id': '112627'
            },
            'name': 'Fajny product',
            'images': ['https://inoxtrade.com.pl/AfterBuy/ats/1.jpg'],
            'parameters': [{
                'name': 'EAN (GTIN)',
                'values': ['8032942644327']
            },
            {
                'name': 'Kod producenta',
                'values': ['123']
            },
            {
                'name': 'Marka',
                'values': ['Testowa superMARKA']
            },
            {
                'name': 'Nazwa handlowa',
                'values': ['Fajny produkt']
            },
            {
                'name': 'Pojemność',
                'values': [350.0]
            },
            {
                'name': 'Produkt nie zawiera',
                'values': ['glutenu']
            }
]}}],
        'images': ['https://inoxtrade.com.pl/AfterBuy/ats/1.jpg', 
                   'https://inoxtrade.com.pl/AfterBuy/ats/2.jpg', 'https://inoxtrade.com.pl/AfterBuy/ats/3.jpg'], 
        'description': {
            'sections': [{
                'items': [{
                    'type': 'IMAGE',
                    'url': 'https://inoxtrade.com.pl/AfterBuy/ats/1.jpg'
                }]}, {
                'items': [{
                    'type': 'TEXT',
                    'content': '<p> Pierwszy blok opisu</p>'
                },
                {
                    'type': 'IMAGE',
                    'url': 'https://inoxtrade.com.pl/AfterBuy/ats/2.jpg'
                }]}, {
                'items': [{
                    'type': 'TEXT',
                    'content': '<p> Drugi blok opisu</p>'
                }]}
            ]},
    'location': {
        'countryCode': 'PL',
        'province': 'MAZOWIECKIE',
        'city': 'Warszawa',
        'postCode': '02-822'
    },
    'stock': {
        'available': 10
    },
    'sellingMode': {
        'format': 'BUY_NOW',
        'price': {
            'amount': '27.43',
            'currency': 'PLN'
        }},
    'payments': {
        'invoice': 'VAT'
    },
    'delivery': {
        'shippingRates': {
            'name': 'Standardowy'
    },
        "handlingTime": "PT48H"
    },
    'afterSalesServices': {
        'id': 'standard'
    }
}

    response = requests.post(url, headers=headers, json=data)

    # print(response.status_code)
    # print(response.json())

    try:
        response_json = response.json()
        print("Response JSON:")
        print(response_json)
    except requests.exceptions.JSONDecodeError:
        print("No JSON response")

    # Additional error handling based on specific use case
    if response.status_code != 200:
        print(f"Error: {response.text}")

    return redirect('index')


def get_orders(request):

    user = get_user(request)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {user.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                print('ERROR RESULT @@@@@@@@@', error_code)
                return redirect('invalid_token')

        print('RESULT @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json()
        }
        return render(request, 'get_orders.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)



def get_one_product(request):

    user = get_user(request)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/7751136519"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {user.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        # return main_categories_result
        print('RESULT @@@@@@@@@', product_result.json())
        context = {
            'result': product_result.json()
        }
        return render(request, 'get_one_product.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def get_ids_all_categories(request):

    user = get_user(request)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/sale/categories"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {user.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        # return main_categories_result
        print('RESULT @@@@@@@@@', product_result.json())
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    