import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .utils import *
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from .models import *

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
    
def success(request, text):
    context = {'text': f'{text}',}
    return render(request, 'success.html', context)


def get_new_authorization_code(request, name):
    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)
    print('******************* name ***********************', secret.CLIENT_ID, account)
    # return HttpResponse('name', name)

    REDIRECT_URI_ =f' http://localhost:8000/get_new_code/{name}&promt=confirm'  

    try: 

        user = get_user(request)

        authorization_redirect_url = AUTH_URL + '?response_type=code&client_id=' + secret.CLIENT_ID + \
                                 '&redirect_uri=' + REDIRECT_URI_ 
        # print("Zaloguj do Allegro - skorzystaj z url w swojej przeglądarce oraz wprowadź authorization code ze zwróconego url: ")
        # print("---  " + authorization_redirect_url + "  ---")

        return redirect(authorization_redirect_url)
    except Exception as e:
        print("An error occurred:", e)
        return redirect('logout_user')


def get_new_code(request, name):
    context = {
        'name': name
    }
    return render(request, 'get_new_code.html', context)

    
def get_code(request):
    return render(request, 'get_code.html')


def get_authorization_code(request):

    REDIRECT_URI_ =' http://localhost:8000/get_code'  

    try: 

        user = get_user(request)

        authorization_redirect_url = AUTH_URL + '?response_type=code&client_id=' + user.CLIENT_ID + \
                                 '&redirect_uri=' + REDIRECT_URI_
        # print("Zaloguj do Allegro - skorzystaj z url w swojej przeglądarce oraz wprowadź authorization code ze zwróconego url: ")
        # print("---  " + authorization_redirect_url + "  ---")

        return redirect(authorization_redirect_url)
    except Exception as e:
        print("An error occurred:", e)
        return redirect('logout_user')
        
    
def get_access_token(request, authorization_code, name):
 
    # user = get_user(request)

    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)

    print('************SECRETS************', secret.CLIENT_ID)

    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': f'http://localhost:8000/get_new_code/{name}'}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=True,
                                              allow_redirects=True, auth=(secret.CLIENT_ID, secret.CLIENT_SECRET))
        print("RESPONSE CONTENT:", access_token_response.status_code)
        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']
        if access_token:
            secret.access_token = access_token
            secret.refresh_token = refresh_token
            secret.save()
            print(f'@#@#@#@# tokens #@#@#@# --------- {tokens}')
            return JsonResponse({
                   'message': tokens,
               })
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    

def get_refresh_token(request, authorization_code):

    account = Allegro.objects.get(user=request.user)
    secret = Secret.objects.get(account=account)

    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': 'http://localhost:8000/get_code'}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(secret.CLIENT_ID, secret.CLIENT_SECRET))
        print("RESPONSE ******* get_refresh_token ******* :", access_token_response)
        print("RESPONSE CONTENT:", access_token_response.status_code)
        tokens = json.loads(access_token_response.text)
        access_token = tokens['refresh_token']
        get_next_token(access_token)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def get_next_token(request, access_token):
    
    account = Allegro.objects.get(user=request.user)
    secret = Secret.objects.get(account=account)

    try:
        data = {'grant_type': 'refresh_token', 'refresh_token': access_token, 'redirect_uri': 'http://localhost:8000/get_code'}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(secret.CLIENT_ID, secret.CLIENT_SECRET))
        print("RESPONSE CONTENT:", access_token_response.status_code)
        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        if access_token:
            secret.access_token = access_token
            secret.save()
            print(f'@#@#@#@# NEXT TOKENS #@#@#@# --------- {tokens}')
            return JsonResponse({
                   'message': tokens,
               })
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)



#################################################################################################################################################
############################################################################ POST NEW PRODUCT ###################################################
#################################################################################################################################################

def post_product(request):

    # account = Allegro.objects.get(user=request.user)
    # secret = Secret.objects.get(account=account)
    token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiIxMDY5NzQ5NzgiLCJzY29wZSI6WyJhbGxlZ3JvOmFwaTpvcmRlcnM6cmVhZCIsImFsbGVncm86YXBpOmZ1bGZpbGxtZW50OnJlYWQiLCJhbGxlZ3JvOmFwaTpwcm9maWxlOndyaXRlIiwiYWxsZWdybzphcGk6c2FsZTpvZmZlcnM6d3JpdGUiLCJhbGxlZ3JvOmFwaTpmdWxmaWxsbWVudDp3cml0ZSIsImFsbGVncm86YXBpOmJpbGxpbmc6cmVhZCIsImFsbGVncm86YXBpOmNhbXBhaWducyIsImFsbGVncm86YXBpOmRpc3B1dGVzIiwiYWxsZWdybzphcGk6c2FsZTpvZmZlcnM6cmVhZCIsImFsbGVncm86YXBpOmJpZHMiLCJhbGxlZ3JvOmFwaTpzaGlwbWVudHM6d3JpdGUiLCJhbGxlZ3JvOmFwaTpvcmRlcnM6d3JpdGUiLCJhbGxlZ3JvOmFwaTphZHMiLCJhbGxlZ3JvOmFwaTpwYXltZW50czp3cml0ZSIsImFsbGVncm86YXBpOnNhbGU6c2V0dGluZ3M6d3JpdGUiLCJhbGxlZ3JvOmFwaTpwcm9maWxlOnJlYWQiLCJhbGxlZ3JvOmFwaTpyYXRpbmdzIiwiYWxsZWdybzphcGk6c2FsZTpzZXR0aW5nczpyZWFkIiwiYWxsZWdybzphcGk6cGF5bWVudHM6cmVhZCIsImFsbGVncm86YXBpOnNoaXBtZW50czpyZWFkIiwiYWxsZWdybzphcGk6bWVzc2FnaW5nIl0sImFsbGVncm9fYXBpIjp0cnVlLCJpc3MiOiJodHRwczovL2FsbGVncm8ucGwuYWxsZWdyb3NhbmRib3gucGwiLCJleHAiOjE3MTI3NzE0OTAsImp0aSI6IjE2MzYxYmMyLTA1Y2MtNGM3OC1hNmY4LWQ5MTJlZjA5MWU2MyIsImNsaWVudF9pZCI6IjBhMTU2NjVmNjI1MjQwMmVhNGVlN2ZiZjU3ZTk4YjlhIn0.Ie44lhvsqJPL_4JkAtV0IVQ8KOpau4j5mDit_kIgduXWb7hnEUT9yZXvSPEjkGvjbSvBXyV0sNVvpur4MmxR0TZBn4TY0i7lr0eDc8C8Fw1SHULsTEwuKZSWbQ7HRvLUp6yMRIfcZRI__RlFE39Z2tQrhfCQSF-bJWqpEgoIMHNi0AfQMU1la-Uz_AXO-aabHFGFUuH-JD-bZWSTM3cpZdjW3VN1nD-A-S261kAYy4DEQO512UN67Q7sjmEuUsoqKbq8JXQoigH8szPSDWamNi83MwwaG_Zz5atJ_z19euiPDEuyHkKXedgki0vXGWeKuI_lGS-sEbdSZJGPhX6JWXMQTtKuYjRjMy7vMYcZaDx7pNnXNo8BskqGgOdNoyhdOik0yGK7UhnP_z7yLmQpgFxegiXShhIg_ouXNWzj4GMcN8BYfOomiLqR0_trFWqeko6uUNagBUqunrIlnwiVmpPfL888DHehAZd8XDkFuWzBASD029IPULxIyBBUOJvOWj7QBis2fH6lMNbUem4-RYyaOE9DcYuymkKdp8QGIzMAlocV2uegqiQaUweaxoDRnE2jjYFRfRd65bwOh-8kgMCUI23kCQR24KZImsUJ_vh1xxXhIq-7SR7fBvUWyEeQ2UHkLIYefh9ucKgWut3ZrWJukfYYogIMtP78kIa8h68'
    
    url = f'https://api.allegro.pl.allegrosandbox.pl/sale/product-offers'

    headers = {
        # 'Authorization': f'Bearer {secret.access_token}',
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }


    
    data = {
    'productSet': [{
        'product': {
            'category': {
                'id': '112627' #'112627'
            },
            'name': 'Fajny product 8',
            'images': ['https://inoxtrade.com.pl/AfterBuy/ats/1.jpg'],
            'parameters': [{
                'name': 'EAN (GTIN)',
                'values': ['5904659181460']
            },
            {
                'name': 'Kod producenta',
                'values': ['008']
            },
            {
                'name': 'Marka',
                'values': ['DK']
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

        'external': {
                'id': '007' #sygnatura
            },

        'images': [ #'https://inoxtrade.com.pl/AfterBuy/ats/1.jpg', 
                   'https://inoxtrade.com.pl/AfterBuy/ats/2.jpg', 'https://inoxtrade.com.pl/AfterBuy/ats/3.jpg'], 
        'description': {
            'sections': [{
                'items': [{
                    'type': 'IMAGE',
                    'url': 'https://inoxtrade.com.pl/AfterBuy/ats/2.jpg'
                }]
                }, 
                {
                    'items': [{
                        'type': 'TEXT',
                        'content': '<p> Pierwszy blok opisu</p>'
                    },
                    {
                        'type': 'IMAGE',
                        'url': 'https://inoxtrade.com.pl/AfterBuy/ats/3.jpg'
                    }]
                }, 
                {
                    'items': [{
                        'type': 'TEXT',
                        'content': '<p> Drugi blok opisu</p>'
                    }]
                },
                {
                    'items': [{
                        'type': 'IMAGE',
                        'url': 'https://inoxtrade.com.pl/AfterBuy/ats/1.jpg'
                    }]
                }
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
            'amount': '37.90',
            'currency': 'PLN'
        }},
    'payments': {
        'invoice': 'VAT'
    },
    "taxSettings": {
    "rates": [
            {
                "rate": "23.00",
                "countryCode": "PL"
            }
        ],
        "subject": "GOODS",
        # "exemption": "MONEY_EQUIVALENT"
    },
    'delivery': {
        'shippingRates': {
            'name': 'Standardowy'
    },
        "handlingTime": "PT48H"
    },
    'afterSalesServices': {
        'id': 'standard'
    },
    "discounts": {
        "wholesalePriceList": {
            # "id": "Hurtowy min",
            "name": "Hurtowy min"
        }
    },
    "messageToSellerSettings": {
        "mode": "OPTIONAL",
        "hint": "Wybierz wzór"
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

    

def get_ids_all_categories(request):

    account = Allegro.objects.get(user=request.user)
    secret = Secret.objects.get(account=account)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/sale/categories"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        # return main_categories_result
        print('RESULT @@@@@@@@@', product_result.json())
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

