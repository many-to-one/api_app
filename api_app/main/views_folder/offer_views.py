import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from ..utils import *
import requests
from ..models import *


def get_all_offers(request, name):

    # print('******* name ********', name)
    account = Allegro.objects.get(name=name)
    # print('******* account ********', account)
    secret = Secret.objects.get(account=account)
    # print('******* secret ********', secret)
    # print('******* secret.access_token ********', secret.access_token)

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
        # print('RESULT - get_all_offers - @@@@@@@@@', json.dumps(result, indent=4))
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

    print('************** get_one_offer id **************', id)

    # account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account__name=name)
    # print('**************secret**************', secret.access_token)
    
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
        # print('RESULT - get_one_offer - @@@@@@@@@', json.dumps(result, indent=4))
        item_height = ""
        item_width = ""
        item_length = ""
        item_wieght = ""
        for item in result["productSet"][0]["product"]["parameters"]:
            if item["id"] == "223329":
                item_height = item["values"][0]
                # print('************** get_one_offer item **************', item["values"][0])
            if item["id"] == "223333":
                item_width = item["values"][0]
            if item["id"] == "201321":
                item_length = item["values"][0]
            if item["id"] == "17448":
                item_wieght = item["values"][0]
        context = {
            'result': product_result.json()
            # "item_height": item_height,
            # "item_width": item_width,
            # "item_length": item_length,
            # "item_wieght": item_wieght,
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
    ean = data.get('ean')

    print('************** name **************', name)
    print('************** lister **************', lister)
    print('************** ean **************', ean)

    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)

    account = Allegro.objects.get(name=lister)
    secret_lister = Secret.objects.get(account=account)
    # print('**************secret**************', secret_lister.access_token)
    
    # return HttpResponse('ok')

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {secret_lister.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        # Headers of the response
        print(" ************* Headers of the response: *************", product_result.headers)
        print('RESULT @@@@@@@@@', result)
        if 'errors' in result:
            # Handle errors in the response
            errors = result['errors']
            print(f"************ ERROR MESSAGE IN ERRORS ************ {errors}")
            for error in errors:
                code = error.get('code')
                message = error.get('message')
                # print(f"************ ERROR MESSAGE IN ERRORS ************ {code}: {message}")
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
        # print('RESULT - post_new_offer - @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json()
        }
        post_data = json.dumps(result, indent=4)
        if len(ean) == 13:
            post_product_from_lister(request, secret, ean, product_result.json())
            return JsonResponse(
            {
                'message': 'Success',
                # 'context': context,
            }, 
            status=200,
        )
        else:
            print('Error 13')
            return JsonResponse(
            {
                'message': 'Error 13',
                'context': 'Error 13',
            }, 
            status=200,
        )
        
        
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

def post_product_from_lister(request, secret, ean, post_data):

    # account = Allegro.objects.get(user=request.user)
    # secret = Secret.objects.get(account=account)

    # print('************** post_data **************', post_data)
    # print('************** ean **************', ean)

    if "delivery" in post_data:
        delivery_info = post_data["delivery"]
        if "shippingRates" in delivery_info:
            delivery_info["shippingRates"]["name"] = "Standard"
            del delivery_info["shippingRates"]["id"]
            # print('************** delivery_info **************', delivery_info)
    name = post_data.get("name")
    # print('************** name **************', name)
    category = post_data.get("category")
    # print('************** category **************', category["id"])

    for product in post_data['productSet']:
        product['product']['name'] = name
        product['product']['images'] = ['https://inoxtrade.com.pl/AfterBuy/ats/1.jpg']

    for product in post_data['productSet']:
        product['product']['category'] = category
    for product in post_data['productSet']:
        for i in product['product']['parameters']:
            if i['id'] == '225693':
                i['values'] = [f"{ean}"]
                print('************** EAN EAN EAN **************', 'TAK', i['values'])
    external = post_data.get("external")
    # print('************** external **************', external)
    images = post_data.get("images")
    # print('************** images **************', images)
    description = post_data.get("description")
    # print('************** description **************', description)
    location = post_data.get("location")
    # print('************** location **************', location)
    stock = post_data.get("stock")
    # print('************** stock **************', stock)
    sellingMode = post_data.get("sellingMode")
    # print('************** sellingMode **************', sellingMode)
    payments = post_data.get("payments")
    # print('************** payments **************', payments)
    taxSettings = post_data.get("taxSettings")
    # print('************** taxSettings **************', taxSettings)
    if "discounts" in post_data:
        discounts = post_data["discounts"]
        discounts["name"] = "Hurtowy min"
        # print('************** discounts **************', discounts)
    if "messageToSellerSettings" in post_data:
        messageToSellerSettings = post_data["messageToSellerSettings"]
        post_data["messageToSellerSettings"] = "OPTIONAL"
        # messageToSellerSettings["hint"] = "Wybierz wzór"
        # print('************** messageToSellerSettings **************', messageToSellerSettings)
    if "afterSalesServices" in post_data:
        afterSalesServices = post_data["afterSalesServices"]
        afterSalesServices["name"] = "Standard"
        del afterSalesServices["impliedWarranty"]["id"]
        del afterSalesServices["returnPolicy"]["id"]
        # print('************** afterSalesServices **************', afterSalesServices)

    print('************** POST DATA **************', json.dumps(post_data["productSet"], indent=4))

    data = {
    'name': name,
    # 'productSet': post_data["productSet"],

    'productSet': [{'product': 
                    {
                        'name': name,
                        'images': ['https://inoxtrade.com.pl/AfterBuy/ats/1.jpg'],
                        'parameters': 
                        post_data["productSet"][0]["product"]["parameters"]
                            # [
                            #     post_data["productSet"][0]["product"]["parameters"][0], 
                            #     post_data["productSet"][0]["product"]["parameters"][1],  
                            #     post_data["productSet"][0]["product"]["parameters"][2], 
                            #     post_data["productSet"][0]["product"]["parameters"][3],  
                            #     post_data["productSet"][0]["product"]["parameters"][4], 
                            #     post_data["productSet"][0]["product"]["parameters"][6],
                            #     {
                            #         'id': '225693', 
                            #         'name': 'EAN (GTIN)', 
                            #         'values': [ean], 
                            #         'valuesIds': None, 
                            #         'rangeValue': None
                            #     }
                            # ]
                        # 'parameters': post_data["productSet"][0]['product']["parameters"][1:] + [
                        #     {
                        #         'id': '225693', 
                        #         'name': 'EAN (GTIN)', 
                        #         'values': [ean], 
                        #         'valuesIds': None, 
                        #         'rangeValue': None
                        #     }
                        # ]
                    }, 
                        # 'quantity': {'value': 1},
                        'responsiblePerson': None
                    }],

    'external': external,  #delayedX czas wydłużenia wystawienia
    'category': category,
    'images': images, 
    'description': description,
    'location': location,
    'stock': stock,
    'sellingMode': sellingMode,
    'payments': payments,
    "taxSettings": taxSettings,
    'delivery': delivery_info,
    'afterSalesServices': afterSalesServices,
    "discounts": {
        "wholesalePriceList": {
            "name": "Hurtowy min"
        }
    },
    "messageToSellerSettings": messageToSellerSettings,
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
        print(response.headers)

        return redirect('index')

    try:
        result = response.json()
        print("Response JSON:")
        print(json.dumps(result, indent=4))
    except requests.exceptions.JSONDecodeError:
        print("No JSON response")

    # return HttpResponse('ok', ean)



def get_ean(request):

    data = json.loads(request.body.decode('utf-8'))
    id = data.get('offerId')
    name = data.get('name')

    print('************** get_ean name **************', name)
    print('************** get_ean offerId **************', id)

    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)
    # print('************** get_ean secret **************', secret.access_token)
    
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
        # print('RESULT - get_one_offer - @@@@@@@@@', json.dumps(result, indent=4))

        values_list = None
        eaN = ''
        if "productSet" in result:
            for product in result.get("productSet", []):
                parameters = product.get("product", {}).get("parameters", [])
                for parameter in parameters:
                    if "EAN" in parameter.get("name", ""):
                        values_list = parameter.get("values", [])
                        print('****************** values_list ********************', values_list[0])
                        break

        context = {
            'result':values_list[0]
        }
        return JsonResponse(
            {
                'message': 'Stock updated successfully',
                'context': context,
            }, 
            status=200,
        )
        
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)



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