import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from ..utils import *
import requests
from ..models import *


def get_all_offers(request, name):

    print('******* name ********', name)
    account = Allegro.objects.get(name=name)
    print('******* account ********', account)
    secret = Secret.objects.get(account=account)
    print('******* secret ********', secret)
    print('******* secret.access_token ********', secret.access_token)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/sale/offers"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        # print('******* product_result ********', result)
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token, name)
                    # Retry fetching orders with the new token
                    return get_all_offers(request, name)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    context = {'name': name}
                    return render(request, 'invalid_token.html', context)
        print('RESULT - get_all_offers - @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json(),
            'name': name,
        }
        return render(request, 'get_all_offers.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    # return HttpResponse ('Ok')
    

def get_one_offer(request, id):

    data = json.loads(request.body.decode('utf-8'))
    name = data.get('name')

    print('**************name**************', name)

    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)
    print('**************secret**************', secret.access_token)
    
    # return HttpResponse('ok')

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token)
                    # Retry fetching orders with the new token
                    return get_one_offer(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')
        print('RESULT - get_one_offer - @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json()
        }
        # post_product_from_lister(request, result)

        # return render(request, 'get_one_offer.html', context)
        return JsonResponse(
            {
                'message': 'Stock updated successfully',
                'context': context,
            }, 
            status=200,
        )
        
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def post_new_offer(request, id):

    data = json.loads(request.body.decode('utf-8'))
    name = data.get('name')
    lister = data.get('lister')

    print('************** name **************', name)
    print('************** lister **************', lister)

    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)

    account = Allegro.objects.get(name=lister)
    secret_lister = Secret.objects.get(account=account)
    print('**************secret**************', secret_lister.access_token)
    
    # return HttpResponse('ok')

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {secret_lister.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token)
                    # Retry fetching orders with the new token
                    return get_one_offer(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')
        print('RESULT - post_new_offer - @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json()
        }
        post_data = json.dumps(result, indent=4)
        post_product_from_lister(request, secret, product_result.json())
        # return render(request, 'get_one_offer.html', context)
        return JsonResponse(
            {
                'message': 'Stock updated successfully',
                'context': context,
            }, 
            status=200,
        )
        
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def post_product_from_lister(request, secret, post_data):

    # account = Allegro.objects.get(user=request.user)
    # secret = Secret.objects.get(account=account)

    # if "delivery" in post_data:
    #     delivery_info = post_data["delivery"]
    #     if "shippingRates" in delivery_info:
    #         delivery_info["shippingRates"]["name"] = "Standard"
    #         del delivery_info["shippingRates"]["id"]
    #     if "messageToSellerSettings" in post_data:
    #         message_settings = post_data["messageToSellerSettings"]
    #         message_settings["mode"] = "OPTIONAL"
    #         message_settings["hint"] = "Wybierz wzór"

    print('************** post_data **************', post_data)
    if "delivery" in post_data:
        delivery_info = post_data["delivery"]
        if "shippingRates" in delivery_info:
            delivery_info["shippingRates"]["name"] = "Standard"
            del delivery_info["shippingRates"]["id"]
            print('************** delivery_info **************', delivery_info)
    productSet = post_data.get("productSet")
    print('************** productSet **************', productSet)
    external = post_data.get("external")
    print('************** external **************', external)
    images = post_data.get("images")
    print('************** images **************', images)
    description = post_data.get("description")
    print('************** description **************', description)
    location = post_data.get("location")
    print('************** location **************', location)
    stock = post_data.get("stock")
    print('************** stock **************', stock)
    sellingMode = post_data.get("sellingMode")
    print('************** sellingMode **************', sellingMode)
    payments = post_data.get("payments")
    print('************** payments **************', payments)
    taxSettings = post_data.get("taxSettings")
    print('************** taxSettings **************', taxSettings)
    if "discounts" in post_data:
        discounts = post_data["discounts"]
        discounts["name"] = "Hurtowy min"
        del discounts["wholesalePriceList"]["id"]
        # del afterSalesServices["returnPolicy"]["id"]
        print('************** discounts **************', discounts)
    if "messageToSellerSettings" in post_data:
        messageToSellerSettings = post_data["messageToSellerSettings"]
        # messageToSellerSettings["mode"] = "OPTIONAL"
        # messageToSellerSettings["hint"] = "Wybierz wzór"
        print('************** messageToSellerSettings **************', messageToSellerSettings)
    if "afterSalesServices" in post_data:
        afterSalesServices = post_data["afterSalesServices"]
        afterSalesServices["name"] = "Standard"
        del afterSalesServices["impliedWarranty"]["id"]
        del afterSalesServices["returnPolicy"]["id"]
        print('************** afterSalesServices **************', afterSalesServices)
    # stock = post_data.get("stock")
    # print('************** product **************', stock)
    # stock = post_data.get("stock")
    # print('************** product **************', stock)
    # stock = post_data.get("stock")
    # print('************** product **************', stock)


# Convert the modified dictionary back to JSON
    # modified_json_data = json.dumps(post_data, indent=4)
    # print('************** modified_json_data **************', modified_json_data)
    # print("Parameters:")
    # for parameter in post_data["productSet"][0]["product"]["parameters"]:
    #     print(parameter["name"] + ":", parameter["values"][0])

    data = {
    'productSet': productSet,

        'external': external,

        'images': images, 
        'description': description,
    'location': location,
    'stock': stock,
    'sellingMode': sellingMode,
    'payments': payments,
    "taxSettings": taxSettings,
    'delivery': delivery_info,
    'afterSalesServices': afterSalesServices,
    "discounts": discounts,
    # "messageToSellerSettings": messageToSellerSettings,
    # "messageToSellerSettings": {
    #     "mode": "OPTIONAL",
    #     "hint": "Wybierz wzór"
    # }
}


    url = f'https://api.allegro.pl.allegrosandbox.pl/sale/product-offers'

    headers = {
        'Authorization': f'Bearer {secret.access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }

    response = requests.post(url, headers=headers, json=data)
    # Additional error handling based on specific use case
    if response.status_code != 200:
        print(f"Error: {response.text}")

        return redirect('index')

    try:
        result = response.json()
        print("Response JSON:")
        print(json.dumps(result, indent=4))
    except requests.exceptions.JSONDecodeError:
        print("No JSON response")



def edit_offer_stock(request, id):

    data = json.loads(request.body.decode('utf-8'))
    new_stock = data.get('stock')
    name = data.get('name')

    print('**************new_stock**************', new_stock)
    print('**************name**************', name)

    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)
    print('**************secret_access_token**************', secret.access_token)
    patch_data = {
        "stock": {
        "available": new_stock,
        "unit": "UNIT"
        },
    }

    # return HttpResponse('ok')

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {
        'Authorization': f'Bearer {secret.access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }
        product_result = requests.patch(url, headers=headers, json=patch_data)
        result = product_result.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token)
                    # Retry fetching orders with the new token
                    return edit_offer_stock(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')
            
        print('RESULT - get_one_offer - @@@@@@@@@', json.dumps(result, indent=4))
        return JsonResponse(
                {
                    'message': 'Stock updated successfully',
                    'newValue': new_stock,
                }, 
                status=200,
            )
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)