import csv
import io
import json, requests
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404

from ..views_folder.api_results import get_all_offers_api
from ..utils import *
from ..models import *
from ..api_service import sync_service


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
            url = "sale/shipping-rates" 
            debug_name = 'get_all_offers 126'

            offers = sync_service.Offers(name)
            result = offers.get_(request, url, debug_name)
            # headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            # product_result = requests.get(url, headers=headers, verify=True)
            # result = product_result.json()
            # # print('******* product_result ********', result)
            # if 'error' in result:
            #     error_code = result['error']
            #     if error_code == 'invalid_token':
            #         # print('ERROR RESULT @@@@@@@@@', error_code)
            #         try:
            #             # Refresh the token
            #             new_token = get_next_token(request, secret.refresh_token, name)
            #             # Retry fetching orders with the new token
            #             return get_all_offers(request, name)
            #         except Exception as e:
            #             print('Exception @@@@@@@@@', e)
            #             context = {'name': name}
            #             return render(request, 'invalid_token.html', context)
            # print('RESULT - shipping_rates - @@@@@@@@@', json.dumps(result, indent=4))
            return result
        except Exception as e:
            return HttpResponse({e})



# GET ALL OFFERS
def get_all_offers(request, name):

    shipping_rates = get_shipping_rates(request, name)
    aftersale_services = get_aftersale_services(request, name)
    
    url = 'sale/offers'
    debug_name = 'get_all_offers 126'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)

    print(' @@@@@@@@@ - get_all_offers - @@@@@@@@@ ', json.dumps(result, indent=4))

    context = {
        'result': result,  
        'name': name,
        'shipping_rates': shipping_rates,
        'aftersale_services': aftersale_services,
    }

    return render(request, 'offers/get_all_offers.html', context)
        
    

# GET OFFER DESCRIPTION
def get_one_offer(request, name, id):

    url = f"sale/product-offers/{id}"
    debug_name = 'get_all_offers 126'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)

    context = {
        'result': result
    }

    return render(request, 'offers/get_one_offer.html', context)

    

def get_description(request, id, name):

    url = f"sale/product-offers/{id}"
    debug_name = 'get_all_offers 126'

    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)

    csv_content = create_csv(result)
    response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8') #, content="pl"
    response['Content-Disposition'] = 'attachment; filename="output.csv"'

    return response
    


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
                        return post_new_offer(request, id)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        return redirect('invalid_token')
            # print('RESULT - post_new_offer - @@@@@@@@@', json.dumps(result, indent=4))
            # context = {
            #     'result': product_result.json()
            # }
            # post_data = json.dumps(result, indent=4)
            if len(ean) == 13:
                post_product_from_lister(request, secret, ean, result)
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

        name = post_data.get("name")
        secret_name = secret.account.name
        shippingRatesName = get_shipping_rates(request, secret_name)
        print('************** shippingRatesName **************', shippingRatesName)
        # print('************** shippingRatesName **************', shippingRatesName['shippingRates'][0]['name'])
        if "delivery" in post_data:
            delivery_info = post_data["delivery"]
            if "shippingRates" in delivery_info:
                delivery_info["shippingRates"]["name"] = shippingRatesName['shippingRates'][0]['name']
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
            afterSalesServices["name"] = get_aftersale_services(request, secret_name) #"Standard"
            del afterSalesServices["impliedWarranty"]["id"]
            del afterSalesServices["returnPolicy"]["id"]
            # print('************** afterSalesServices **************', afterSalesServices)

        # print('************** POST DATA **************', json.dumps(post_data, indent=4))

        data = {
        'name': name,
        'productSet': [{'product': 
                        {
                            'name': name,
                            'images': ['https://inoxtrade.com.pl/AfterBuy/ats/1.jpg'],
                            'parameters': 
                            post_data["productSet"][0]["product"]["parameters"]
                        }, 
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
        
        url = f"sale/product-offers"
        debug_name = 'post_product_from_lister 310'

        offers = sync_service.Offers(secret_name)
        offers.post_(request, url, data, debug_name)




def get_ean(request):

    if request.user.is_authenticated:

        data = json.loads(request.body.decode('utf-8'))
        id = data.get('offerId')
        name = data.get('name')
        
        url = f"sale/product-offers/{id}"
        debug_name = 'get_all_offers 126'

        offers = sync_service.Offers(name)
        result = offers.get_(request, url, debug_name)

        values_list = None
        if "productSet" in result:
            for product in result.get("productSet", []):
                parameters = product.get("product", {}).get("parameters", [])
                for parameter in parameters:
                    if "EAN" in parameter.get("name", ""):
                        values_list = parameter.get("values", [])
                        # print('****************** values_list ********************', values_list[0])
                        break

        context = {
            'result': values_list[0]
        }
        return JsonResponse(
            {
                'message': 'Stock updated successfully',
                'context': context,
            }, 
            status=200,
        )



def edit_offer_patch(request, id):

    data = json.loads(request.body.decode('utf-8'))
    new_stock = data.get('stock')
    new_costs = data.get('costs')
    currency = data.get('currency')
    status = data.get('status')
    title = data.get('title')
    name = data.get('name')

    patch_data = {
        "stock": {
        "available": new_stock,
        "unit": "UNIT"
        },
    }

    if title:
        patch_data = {
             "name": title,
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

    print('############# patch_data #############', patch_data)

    url = f"sale/product-offers/{id}"
    debug_name = 'edit_offer_patch 451'

    offers = sync_service.Offers(name)
    result = offers.patch_(request, url, patch_data, debug_name)

    if list(result.keys())[0] != 'errors':
        return JsonResponse(
            {
                'message': 'Item updated successfully',
                'newTitle': title,
                'newValue': new_stock,
                'newCosts': new_costs,
                'status': 200 #product_result.status_code,
            }, 
            status=200,
        )
    else:
        return JsonResponse(
            {
                'message': result,
                'UserMessage': 'Coś poszło nie tak'
            },
            status=202
        )
    
        

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
