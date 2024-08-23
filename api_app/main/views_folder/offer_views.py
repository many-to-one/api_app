import csv
import io
import json, requests
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404

from .api_results import get_all_offers_api
from ..utils import *
from ..models import *


async def return_async_offer(request, secret, id):

    ''' 
     This function returns a json description of the offer by id into the bulk_editview.py
     to download all offers like json file. Next step is to create async logic for bulk operation
    '''

    if request.user.is_authenticated:

        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
                headers = {'Authorization': f'Bearer {secret}', 'Accept': "application/vnd.allegro.public.v1+json"}
                product_result = await client.get(url, headers=headers)
                result = product_result.json()

                if 'error' in result:
                    error_code = result['error']
                    if error_code == 'invalid_token':
                        return redirect('invalid_token')
                # print('RESULT - download_all_offers - @@@@@@@@@', json.dumps(result, indent=4))

                return  result       
            
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)



# async def return_async_offer(request, secret, id):

#     ''' 
#      This function returns a json description of the offer by id into the bulk_editview.py
#      to download all offers like json file. Next step is to create async logic for bulk operation
#     '''

#     if request.user.is_authenticated:

#         try:
#             url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
#             headers = {'Authorization': f'Bearer {secret}', 'Accept': "application/vnd.allegro.public.v1+json"}
#             product_result = requests.get(url, headers=headers)
#             result = product_result.json()
#             if 'error' in result:
#                 error_code = result['error']
#                 if error_code == 'invalid_token':
#                     return redirect('invalid_token')
#             print('RESULT - download_all_offers - @@@@@@@@@', json.dumps(result, indent=4))
#             return  result       
            
#         except requests.exceptions.HTTPError as err:
#             raise SystemExit(err)



async def download_all_offers(request, offers, secret):

    tasks = []

    for id in offers:
        print('@@@@@@@@@ - download_all_offers id - @@@@@@@@@', id)
        tasks.append(asyncio.create_task(return_async_offer(request, secret, id)))

    # [tasks.append(asyncio.create_task(return_async_offer(request, secret, id))) for id in offers]

    results = await asyncio.gather(*tasks)

    # print('RESULT - download_all_offers - @@@@@@@@@', json.dumps(results, indent=4))

    return results



def get_aftersale_services(request, name):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)

        try:
            url = "https://api.allegro.pl.allegrosandbox.pl/after-sales-service-conditions/return-policies"  
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
            # print('RESULT - get_aftersale_services - @@@@@@@@@', json.dumps(result, indent=4))
            return result
        except Exception as e:
            return HttpResponse({e})



def get_shipping_rates(request, name):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)

        try:
            url = "https://api.allegro.pl.allegrosandbox.pl/sale/shipping-rates" 
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
            # print('RESULT - shipping_rates - @@@@@@@@@', json.dumps(result, indent=4))
            return result
        except Exception as e:
            return HttpResponse({e})




def get_all_offers(request, name):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=name)
        shipping_rates = get_shipping_rates(request, name)
        aftersale_services = get_aftersale_services(request, name)
        # result = get_all_offers_api(request, name)
        # print(" ############### get_all_offers_api ################## ", result[0])
        try:
            url = "https://api.allegro.pl.allegrosandbox.pl/sale/offers"
            # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            product_result = requests.get(url, headers=headers, verify=True)
            result = product_result.json()
            # for of in result['offers']:
                # print('******* get_all_offers ********', of)
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    # print('ERROR RESULT @@@@@@@@@', error_code)
                    try:
                        # Refresh the token
                        new_token = get_next_token(request, secret.refresh_token, name)
                        print('ZADZIAŁAŁO', new_token)
                        if new_token:
                            # Retry fetching orders with the new token
                            return get_all_offers_api(request, name)
                        else:
                            print('COŚ POSZŁO NIE TAK', new_token)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': name}
                        return render(request, 'invalid_token.html', context)
            # print(" ############### shipping_rates ################## ", shipping_rates)
            # print(" ############### product_result.json() API ################## ", product_result.json())
            context = {
                'result': result,  #product_result.json(),
                'name': name,
                'shipping_rates': shipping_rates,
                'aftersale_services': aftersale_services,
            }
            return render(request, 'get_all_offers.html', context)

        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        
    else:
        return redirect('login_user')
    

def get_one_offer(request, id):

    if request.user.is_authenticated:

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
    

def get_description(request, id, lister):

    if request.user.is_authenticated:

        secret = Secret.objects.get(account__name=lister)

        # print(f"************ get_description ************ {lister}, {secret}")

        try:
            url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{id}"
            headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            product_result = requests.get(url, headers=headers, verify=True)
            result = product_result.json()
            # Headers of the response
            # print(" ************* Headers of the response: *************", product_result.headers)
            # print('RESULT @@@@@@@@@', result)
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
            # print('RESULT - get_description - @@@@@@@@@', json.dumps(result, indent=4))

            csv_content = create_csv(result)
            response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8') #, content="pl"
            response['Content-Disposition'] = 'attachment; filename="output.csv"'
            return response
        
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    


def create_csv(json_data):

    ########### SAVE FILE IN THE APP LOGIC ###############
    # Specify the CSV file name
    # csv_file_name = "output.csv"

    # # Open the CSV file in write mode
    # with open(csv_file_name, 'w', newline='') as csv_file:

    #     csv_writer = csv.writer(csv_file)

    #     headers = json_data.keys()
    #     # print('+++++++++ headers ++++++++', headers)
    #     csv_writer.writerow(headers)

    #     rows = json_data.values()
    #     # print('+++++++++ headers ++++++++', rows)
    #     csv_writer.writerow(rows)
    #######################################################    

    #######################################################
    ########### OPEN FILE IN THE BROWSER LOGIC ############
    # Create an in-memory file-like object
    output = io.StringIO()

    csv_writer = csv.DictWriter(output, fieldnames=json_data.keys())
        
    # Write the header
    csv_writer.writeheader()

    # Write the single row
    csv_writer.writerow(json_data)
    csv_content = output.getvalue()
    
    # Close the in-memory file
    output.close()
    
    return csv_content




def post_new_offer(request, id):

    if request.user.is_authenticated:

        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name')
        lister = data.get('lister')
        ean = data.get('ean')

        # print('************** name **************', name)
        # print('************** lister **************', lister)
        # print('************** ean **************', ean)
        print('************** post_new_offer id **************', id)

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
            # print(" ************* Headers of the response: *************", product_result.headers)
            # print('RESULT @@@@@@@@@', result)
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

    if request.user.is_authenticated:

        # account = Allegro.objects.get(user=request.user)
        # secret = Secret.objects.get(account=account)

        print('************** POST DATA **************', post_data)
        # print('************** ean **************', ean)

        name = post_data.get("name")
        if "delivery" in post_data:
            delivery_info = post_data["delivery"]
            if "shippingRates" in delivery_info:
                delivery_info["shippingRates"]["name"] = get_shipping_rates(request, name) #"Standard"
                del delivery_info["shippingRates"]["id"]
                # print('************** delivery_info **************', delivery_info)
        # name = post_data.get("name")
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
            afterSalesServices["name"] = get_aftersale_services(request, name) #"Standard"
            del afterSalesServices["impliedWarranty"]["id"]
            del afterSalesServices["returnPolicy"]["id"]
            # print('************** afterSalesServices **************', afterSalesServices)

        # print('************** POST DATA **************', json.dumps(post_data, indent=4))

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
            print(f"Error: {response.status_code}")
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

    if request.user.is_authenticated:

        data = json.loads(request.body.decode('utf-8'))
        id = data.get('offerId')
        name = data.get('name')

        # print('************** get_ean name **************', name)
        # print('************** get_ean offerId **************', id)

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
                            # print('****************** values_list ********************', values_list[0])
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

    if request.user.is_authenticated:

        data = json.loads(request.body.decode('utf-8'))
        new_stock = data.get('stock')
        new_costs = data.get('costs')
        currency = data.get('currency')
        status = data.get('status')
        name = data.get('name')

        # print('**************new_stock**************', new_stock)
        # print('**************new_costs**************', new_costs)
        # print('**************currency**************', currency)
        # print('**************status**************', status)
        # print('**************name**************', name)

        # account = Allegro.objects.get(name=name)
        secret = Secret.objects.get(account__name=name)

        # print('**************secret_access_token**************', secret.access_token)
        patch_data = {
            "stock": {
            "available": new_stock,
            "unit": "UNIT"
            },
        }

        if new_costs:
            patch_data = {
                "sellingMode": {
                    "format": "BUY_NOW",
                    "price": {
                    "amount": new_costs,
                    "currency": currency,
                    },

                },
            }

        if status:
            patch_data = {
                "publication": {
                    "status": status,
                }
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
                
            # print('RESULT - get_one_offer - @@@@@@@@@', json.dumps(result, indent=4))
            return JsonResponse(
                    {
                        'message': 'Stock updated successfully',
                        'newValue': new_stock,
                        'newCosts': new_costs,
                        'status': status,
                    }, 
                    status=200,
                )
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    


def edit_offers_csv(request, name):

    if request.user.is_authenticated:

        print(' ##################### edit_offers_csv ##################### ', name)

        secret = Secret.objects.get(account__name=name)

        if request.method == 'POST':
            # Check if the file is in the request
            if 'file' in request.FILES:
                csv_file = request.FILES['file']
                
                # Ensure it's a CSV file
                if not csv_file.name.endswith('.csv'):
                    return HttpResponse('This is not a CSV file')
                
                # Read and decode the CSV file
                data_set = csv_file.read().decode('UTF-8')
                # print(' ##################### @ data_set @ ##################### ', data_set)
                io_string = io.StringIO(data_set)
                csv_reader = csv.DictReader(io_string, delimiter=';')  # Use DictReader for automatic header handling

                # csv_data = list(csv_reader)
                # data = [row for row in csv_reader]
                kes_ = []
                for row in csv_reader:
                    for k,v in row.items():
                        print(' ##################### @ row k @ ##################### ', k)
                        print(' ##################### @ row v @ ##################### ', v)
                json_data = json.dumps(row, ensure_ascii=False, indent=4)
                # Convert CSV rows to a list of dictionaries
                # json_data_ = json.dumps(csv_data, ensure_ascii=False, indent=4)
                # print(' ##################### data_set ##################### ', csv_file)
                # mock_file = MockFile(name='example.csv', content=json_data_.encode('utf-8'))
                # print(' ##################### mock_file ##################### ', mock_file)
                # processed_json = process_uploaded_csv(mock_file)
                
                # Convert the list of dictionaries to a JSON string
                # json_data = json.dumps(data, ensure_ascii=False, indent=4)
                # json_data = json.dumps(processed_json, ensure_ascii=False, indent=4)
                # print(' ##################### @ json_data @ ##################### ', json_data)

            
                # json.dumps(data, indent=4) logic

                res = edit_product(request, secret, json_data)
                return HttpResponse(res)
                
                # Return JSON response
                # return HttpResponse(json_data, content_type='application/json')
            else:
                return HttpResponse('No file uploaded', status=400)
        else:
            # Render the upload form if not POST request
            # return render(request, 'your_template.html')
            return HttpResponse('Something wents wrong...')
    
import ast
def edit_product(request, secret, json_data):

    if request.user.is_authenticated:

        json_data_plus = json_data #json_data[0]
        jsnd = ast.literal_eval(json_data_plus)
        # print(' ##################### jsnd ##################### ', jsnd)
        # print(' ##################### type jsnd ##################### ', type(jsnd))

        # print(' ##################### type ##################### ', type(json_data[0]))
        # print(' ##################### secret ##################### ', secret.access_token) #[0]['productSet']
        # json_id = json_data[0]['productSet']
        # id = ast.literal_eval(json_id)
        # print(' ##################### ID liter ##################### ', id[0]['product']['id'])  #['product']['id']

        # edit_offer_stock(request, json_data[0]['id'], json_data)
        return edit_edit(request, secret, [jsnd])

def edit_edit(request, secret, json_data):

    if request.user.is_authenticated:

        # print(' ##################### type ##################### ', type(json_data))

        # name = json_data[0]['name']
        # product_name = ast.literal_eval(name)

        productSet = json_data[0]['productSet']
        product_id = ast.literal_eval(productSet)

        category = json_data[0]['category']
        category_id = ast.literal_eval(category)

        stock = json_data[0]['stock']
        stock_available = ast.literal_eval(stock)

        publication = json_data[0]['publication']
        publication_data = ast.literal_eval(publication)

        additionalMarketplaces = json_data[0]['additionalMarketplaces']
        additionalMarketplaces_data = ast.literal_eval(additionalMarketplaces)

        discounts = json_data[0]['discounts']
        discounts_data = ast.literal_eval(discounts)

        sellingMode = json_data[0]['sellingMode']
        sellingMode_data = ast.literal_eval(sellingMode)

        location = json_data[0]['location']
        location_data = ast.literal_eval(location)

        images = json_data[0]['images']
        images_data = ast.literal_eval(images)

        description = json_data[0]['description']
        description_data = ast.literal_eval(description)

        tax = json_data[0]['tax']
        tax_data = ast.literal_eval(tax)

        taxSettings = json_data[0]['taxSettings']
        taxSettings_data = ast.literal_eval(taxSettings)

        # category = json_data[0]['category']
        # json_compatible_str = category.replace("'", '"')
        # parsed_dict = json.loads(json_compatible_str)
        # category_id = parsed_dict['id']

        # stock = json_data[0]['stock']
        # stock_str = stock.replace("'", '"')
        # stock_dict = json.loads(stock_str)
        # stock_available = stock_dict['available']

        try:
            # print(' ##################### product_name ##################### ', json_data[0]['name'])
            # print(' ##################### stock_available ##################### ', stock_available['available'])
            url = f"https://api.allegro.pl.allegrosandbox.pl/sale/product-offers/{json_data[0]['id']}"
            # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
            headers = {
                'Authorization': f'Bearer {secret.access_token}',
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Content-Type': 'application/vnd.allegro.public.v1+json'
            }
            edit_data = {
    "productSet": [
        {
        "product": {
            "name": 'Test', #json_data[0]['name'],
            "category": category_id,
            "id": product_id[0]['product']['id'],
            "idType": "GTIN",
            # "parameters": json_data[0]['parameters'],
            # "images": json_data[0]['images']
        },
        #   "quantity": {
        #     "value": stock_available['available']
        #   },
        #   "responsiblePerson": {
        #     "id": "string",
        #     "name": "string"
        #   }
        }
    ],
    #   "b2b": json_data[0]['b2b'],
    #   "b2b": {
    #     "buyableOnlyByBusiness": false
    #   },
    #   "attachments": [
    #     {
    #       "id": "string"
    #     }
    #   ],
    #   "fundraisingCampaign": {
    #     "id": "string",
    #     "name": "string"
    #   },
    # "additionalServices": json_data[0]['additionalServices'],
    #   "additionalServices": {
    #     "id": "string",
    #     "name": "string"
    #   },
    #   "compatibilityList": {
    #     "items": [
    #       {
    #         "type": "TEXT",
    #         "text": "CITROËN C6 (TD_) 2005/09-2011/12 2.7 HDi 204KM/150kW"
    #       }
    #     ]
    #   },
    #   "delivery": {
    #     "handlingTime": "PT24H",
    #     # "shippingRates": null,
    #     "additionalInfo": "string",
    #     "shipmentDate": "2019-08-24T14:15:22Z"
    #   },
    "stock": stock_available,
    "publication":publication_data,
    #   "publication": {
    #     "duration": "PT24H",
    #     "endingAt": "2031-01-04T11:01:59Z",
    #     "startingAt": "2031-01-04T11:01:59Z",
    #     "status": "INACTIVE",
    #     "endedBy": "USER",
    #     "republish": false,
    #     "marketplaces": {}
    #   },
    "additionalMarketplaces": additionalMarketplaces_data,
    #   "additionalMarketplaces": {
    #     "allegro-cz": {
    #       "sellingMode": {
    #         "price": {
    #           "amount": "233.01",
    #           "currency": "CZK"
    #         }
    #       }
    #     }
    #   },
    #   "language": "pl-PL",
    #   "category": {
    #     "id": "257931"
    #   },
    #   "parameters": [
    #     {
    #       "id": "string",
    #       "name": "string",
    #       "rangeValue": {
    #         "from": "string",
    #         "to": "string"
    #       },
    #       "values": [
    #         "string"
    #       ],
    #       "valuesIds": [
    #         "string"
    #       ]
    #     }
    #   ],
    #   "afterSalesServices": json_data[0]['afterSalesServices'],
    #   "afterSalesServices": {
    #     "impliedWarranty": {
    #       "id": "09f0b4cc-7880-11e9-8f9e-2a86e4085a59",
    #       "name": "string"
    #     },
    #     "returnPolicy": {
    #       "id": "09f0b4cc-7880-11e9-8f9e-2a86e4085a59",
    #       "name": "string"
    #     },
    #     "warranty": {
    #       "id": "09f0b4cc-7880-11e9-8f9e-2a86e4085a59",
    #       "name": "string"
    #     }
    #   },
    #   "sizeTable": {
    #     "id": "string",
    #     "name": "string"
    #   },
    #   "contact": json_data[0]['contact'], bo ""
    #   "contact": {
    #     "id": "string",
    #     "name": "string"
    #   },
    "discounts": discounts_data,
    #   "discounts": {
    #     "wholesalePriceList": {
    #       "id": "string",
    #       "name": "string"
    #     }
    #   },
    #   "name": "string",
    #   "payments": {
    #     "invoice": "VAT"
    #   },
    "sellingMode": sellingMode_data,
    #   "sellingMode": {
    #     "format": "BUY_NOW",
    #     "price": {
    #       "amount": "123.45",
    #       "currency": "PLN"
    #     },
    #     "minimalPrice": {
    #       "amount": "123.45",
    #       "currency": "PLN"
    #     },
    #     "startingPrice": {
    #       "amount": "123.45",
    #       "currency": "PLN"
    #     }
    #   },
    "location": location_data,
    #   "location": {
    #     "city": "string",
    #     "countryCode": "PL",
    #     "postCode": "00-999",
    #     "province": "string"
    #   },
    "images": images_data,
    #   "images": [
    #     "string"
    #   ],
    "description": description_data,
    #   "description": {
    #     "sections": [
    #       {
    #         "items": [
    #           {
    #             "type": "string"
    #           }
    #         ]
    #       }
    #     ]
    #   },
    #   "external": {
    #     "id": "AH-129834"
    #   },
    "tax": tax_data,
    #   "tax": {
    #     "id": "ae727432-8b72-4bfe-b732-6f163a2bf32a",
    #     "rate": "23.00",
    #     "subject": "GOODS",
    #     "exemption": "MONEY_EQUIVALENT",
    #     "percentage": "23.00"
    #   },
    "taxSettings": taxSettings_data,
    #   "taxSettings": {
    #     "rates": [
    #       {
    #         "rate": "23.00",
    #         "countryCode": "PL"
    #       }
    #     ],
    #     "subject": "GOODS",
    #     "exemption": "MONEY_EQUIVALENT"
    #   },
    #   "messageToSellerSettings": {
    #     "mode": "OPTIONAL",
    #     "hint": "string"
    #   }
    }
            product_result = requests.patch(url, headers=headers, json=edit_data)
            result = product_result.json()

            # Headers of the response
            print(" ************* Headers of the response: *************", product_result.headers)
            # print(" ************* response body: *************", product_result.body)
            print(" ************* response: *************", product_result)
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
            # print('RESULT - edit_edit - @@@@@@@@@', json.dumps(result, indent=4))
            return HttpResponse(
                    {
                        'message': 'offer edited successfuly',
                        # 'newValue': result.staus,
                        'result': result,
                    }, 
                    status=200,
                )
        # except Exception as err:
        #     return HttpResponse({'HttpResponse Exception @@@@@@@@@': err})
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        

# Measure CPU and memory usage
# def measure_resources(*args, **kwargs):
#     # Measure memory usage before and after the function execution
#     mem_before = psutil.Process().memory_info().rss / 1024 / 1024  # in MB
#     cpu_before = psutil.cpu_percent(interval=0.1)

#     start_time = time.time()
#     mem_usage_before = memory_usage(-1, interval=0.1, timeout=1)

#     result = func(*args, **kwargs)

#     mem_usage_after = memory_usage(-1, interval=0.1, timeout=1)
#     end_time = time.time()

#     mem_after = psutil.Process().memory_info().rss / 1024 / 1024  # in MB
#     cpu_after = psutil.cpu_percent(interval=0.1)

#     elapsed_time = end_time - start_time

#     print(f"Function result: {result}")
#     print(f"Time taken: {elapsed_time:.2f} seconds")
#     print(f"Memory usage before: {mem_before:.2f} MB")
#     print(f"Memory usage after: {mem_after:.2f} MB")
#     print(f"Peak memory usage: {max(mem_usage_after) - min(mem_usage_before):.2f} MB")
#     print(f"CPU usage before: {cpu_before:.2f}%")
#     print(f"CPU usage after: {cpu_after:.2f}%")

    

def upload_json_offers(request, shipping_rates_id, after_sale_id, vat):

    start_time = time.time()
    
    if request.method == 'POST':
        if not request.FILES.get('jsonFile'):
            return HttpResponseBadRequest('No file uploaded.')

        json_file = request.FILES['jsonFile']
        offers = json.load(json_file)
        # shipping_rates_id = request.headers.get('X-Selected-Method-Id')
        # after_sale_id = request.headers.get('X-Selected-Warranty-Id')
        name = request.POST.get('name')
        secret = Secret.objects.get(account__name=name)

        # print('********************** upload_json_offers offers ****************************', json.dumps(offers[0], indent=4))
        # print('********************** IDS name ****************************', name)
        # print('********************** shipping_rates_id ****************************', shipping_rates_id)
        # print('********************** after_sale_id ****************************', after_sale_id)
        # print('********************** VAT ****************************', vat)

        res = asyncio.run(post_uploaded_products(offers, shipping_rates_id, after_sale_id, vat, secret.access_token))

        if res:
            end_time = time.time()
            elapsed_time = end_time - start_time
            print('********************** FUNCTION TIME ****************************', elapsed_time)
            
        return JsonResponse({
            "message": 'Success',
            "status": 200 ,
        })

        # return redirect('get_all_offers', name=name)

async def post_uploaded_products(offers, shipping_rates_id, after_sale_id, vat, secret_access_token):

    tasks = []

    res = [
        tasks.append(asyncio.create_task(post_product(offer, shipping_rates_id, after_sale_id, vat, secret_access_token)))
        for offer in offers
    ]

    # for offer in offers:
    #         # print('********************** offer shippingRates id ****************************', offer['delivery']['shippingRates']['id'])
    #         # print('********************** offer afterSalesServices ****************************', offer['afterSalesServices'])
    #         tasks.append(asyncio.create_task(post_product(offer, shipping_rates_id, after_sale_id, vat, secret_access_token)))

    await asyncio.gather(*tasks)



async def post_product(offer, shipping_rates_id, after_sale_id, vat, secret_access_token):

    # async with httpx.AsyncClient() as client:
    url = f'https://api.allegro.pl.allegrosandbox.pl/sale/product-offers'

    headers = {
        'Authorization': f'Bearer {secret_access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }

    data = offer

    data["delivery"] = {
        "shippingRates": {
            "id": shipping_rates_id
        },
        # "handlingTime": "PT24H",
        # "additionalInfo": null,
        # "shipmentDate": null
    }
    data["tax"] = None
    data["taxSettings"]["subject"] = "GOODS"
    data["taxSettings"]["rates"][0]["rate"] = vat
    data["afterSalesServices"] = {
        # "impliedWarranty": {
        #     "id": "fce22b92-b86e-4cbf-a9ba-7cff4e92fb12"
        # },
        "returnPolicy": {
            "id": after_sale_id
        }
        # "warranty": None
    }
    data["discounts"] = None


    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        response_json = response.json()

    # print(response.status_code)
    # print(response.json())

    try:
        response_json = response.json()
        # print("Response JSON:")
        # print(response_json)
    except requests.exceptions.JSONDecodeError:
        print("No JSON response")

    # Additional error handling based on specific use case
    if response.status_code != 200:
        print(f"Error: {response.status_code}")

    return redirect('index')
