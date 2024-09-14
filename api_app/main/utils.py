import asyncio
import math
import time
from users.models import CustomUser
from users.views import logout_user
from .models import *
import requests
from django.http import JsonResponse
import json
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN_URL = os.getenv('TOKEN_URL')
import httpx
from django.shortcuts import redirect


async def check_login(request):
    if request.user.is_authenticated:
        return True
    else:
        return redirect('login')
        


def get_user(request):
    user = CustomUser.objects.get(id=request.user.id)
    return user


async def get_token():
    secret = Secret.objects.get(account__name='retset')
    return secret.access_token


def get_next_token(request, access_token, name):

    print(f'@#@#@#@# get_next_token access_token #@#@#@# --------- {access_token}')
    
    # account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account__name=name)
    print(f'@#@#@#@# secret #@#@#@# --------- {secret}')

    # try:
    data = {'grant_type': 'refresh_token', 'refresh_token': secret.refresh_token, 'redirect_uri': 'http://localhost:8000/get_code'}
    access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                          allow_redirects=True, auth=(secret.CLIENT_ID, secret.CLIENT_SECRET))
    print("RESPONSE CONTENT:", access_token_response)
    tokens = json.loads(access_token_response.text)
    print("RESPONSE CONTENT:", type(tokens))
    print(f'@#@#@#@# NEXT TOKENS #@#@#@# --------- {tokens}')
    access_token = tokens['access_token']
    print(f'@#@#@#@# NEXT TOKENS REPEAT #@#@#@# --------- {access_token}')
    # error_token = tokens['error']
    # refresh_token = tokens['refresh_token']
    if access_token:
        print(f'@#@#@#@# NEXT TOKENS REPEAT II #@#@#@# --------- {access_token}')
        secret.access_token = access_token
        # secret.refresh_token = refresh_token
        secret.save()
        # print(f'@#@#@#@# NEXT TOKENS #@#@#@# --------- {access_token}')
        print(' ************* NEXT TOKEN WAS CREATED ************* ', secret)
        return access_token
    if tokens['error']:
        print(f'@#@#@#@# NEXT TOKENS ERROR ERROR ERROR #@#@#@# --------- ', tokens['error'])
        # If the exceptions will repeat, I need to create logic
        # to get a new token o smth to login to allegro 
        # via secret.CLIENT_ID, secret.CLIENT_SECRET
        # to get a new access/refresh_token
        return redirect(logout_user())
            
    # except requests.exceptions.HTTPError as err:
    #     # raise SystemExit(err)
    #     print(f'******** requests.exceptions.HTTPError ******** --------- {err}')










######################################################################################################################
#################################################### CREATE ORDER ####################################################
######################################################################################################################

async def test(secret, order_data, external_id, offer_name, descr, user, packageTypes):
    print('********************** USER TEST ****************************', user)
    print('********************** packageTypes TEST ****************************', packageTypes)
    result = None
    if order_data["delivery"]["pickupPoint"] == None:
        if order_data["payment"]["type"] == 'CASH_ON_DELIVERY': 
            result = await cash_no_point_order(secret, order_data, external_id, offer_name, descr, user, packageTypes)
        else:
            result = await no_pickup_point_order(secret,  order_data, external_id, offer_name, descr, user, packageTypes)
    else:
        if order_data["payment"]["type"] == 'CASH_ON_DELIVERY': 
            result = await cash_no_point_order(secret,  order_data, external_id, offer_name, descr, user, packageTypes)
        # print('********************** pickupPoint ****************************', order_data["delivery"]["pickupPoint"])
        else:
            # result = pickup_point_order(secret,  order_data, external_id, offer_name, descr)
            result = await pickup_point_order(secret,  order_data, external_id, offer_name, descr, user, packageTypes)

    return result

async def pickup_point_order(secret, order_data, external_id, offer_name, descr, user, packageTypes):

    """ With pick up from seller """

    if order_data["delivery"]["method"]["name"] == "Allegro Automat DHL POP BOX":
      order_data["delivery"]["pickupPoint"]["id"] = 4591097 #/ 4594563
    if order_data["delivery"]["method"]["name"] ==  "Allegro Odbiór w Punkcie DHL":
        order_data["delivery"]["pickupPoint"]["id"] = 4509455

    # print(' ######################### pickup_point_order secret ######################### ', secret.access_token)
    # print(' ######################### pickup_point_order order_data ######################### ', order_data["delivery"]["pickupPoint"]["id"]) 
    print(' ######################### pickup_point_order external_id ######################### ', len(external_id))
    print(' ######################### pickup_point_order delivery pickupPoint id ######################### ', order_data["delivery"]["pickupPoint"]["id"])
    print(' ######################### pickup_point_order delivery method id ######################### ', order_data["delivery"]["method"]["id"])
    print(' ######################### pickup_point_order offer_name ######################### ', order_data["delivery"]["address"]["phoneNumber"])
    print(' ######################### pickup_point_order descr + ######################### ', descr[3])
    
    description = external_id
    if len(external_id) > 20: # description (1 x 007-81) can't has more than 20 symbols
        description = ''
    length_value = descr[0]
    if descr[0] == '':
        length_value = 20
    width_value = descr[1]
    if descr[1] == '':
        width_value = 20
    height_value = descr[2]
    if descr[2] == '':
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            height_value = 2
        else:
          height_value = 5
    if descr[3] != '':
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            weight_value = 0.5
        else:
          weight_value = math.ceil(float(descr[3]))
    else:
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            weight_value = 0.5
        else:
          weight_value = 1

    delivery_name = order_data["delivery"]["method"]["name"] 
    delivery_name = delivery_name.replace('ł', 'l').replace('ó', 'o').replace('ż', 'z').replace(',', '').replace('.', ' ').replace('(', ' ').replace(')', ' ')
    # print(' ######################### pickup_point_order delivery_name ######################### ', delivery_name)
      
    # order_data["delivery"]["address"]["phoneNumber"] = "500600700"
    async with httpx.AsyncClient() as client:  
      url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/shipments/create-commands"
      headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
      payload = {
                  # "commandId": "",
                  "input": {
                    "deliveryMethodId": order_data["delivery"]["method"]["id"],
                    # "credentialsId": "", #"b20ef9e1-faa2-4f25-9032-adbea23e5cb9#abcdef-ghij-klmn-opqrs123",#b20ef9e1-faa2-4f25-9032-adbea23e5cb9#
                    "sender": {
                      "name": f"{user['firstName']} {user['lastName']}",
                      "company": user['company'],
                      "street": user['street'],
                      "streetNumber": user['streetNumber'],
                      "postalCode": user['postalCode'], #"52-340"(kod Wrocław),
                      "city": user['city'],
                      # "state": "AL",
                      "countryCode": "PL",
                      "email": user['email'],#"8awgqyk6a5+cub31c122@allegrogroup.pl",
                      "phone": user['phone'], #"+48500600700",
                    },
                    "receiver": {
                      "name": f'{order_data["buyer"]["firstName"]} {order_data["buyer"]["lastName"]}',#"Jan Kowalski"
                      "company": order_data["buyer"]["companyName"],
                      "street": order_data["buyer"]["address"]["street"].split()[0],
                      "streetNumber": order_data["buyer"]["address"]["street"].split()[1],
                      "postalCode": order_data["buyer"]["address"]["postCode"],
                      "city": order_data["buyer"]["address"]["city"],
                      # "state": "AL",
                      "countryCode": order_data["buyer"]["address"]["countryCode"],
                      "email": order_data["buyer"]["email"],
                      "phone": order_data["delivery"]["address"]["phoneNumber"], #str(order_data["delivery"]["address"]["phoneNumber"]), #+48500600700"
                      "point": order_data["delivery"]["pickupPoint"]["id"] #4591097 
                    },
                    "pickup": {
                      "name": f"{user['firstName']} {user['lastName']}",
                      "company": user['company'],
                      "street": user['street'],
                      "streetNumber": user['streetNumber'],
                      "postalCode": user['postalCode'], #"52-340"(kod Wrocław),
                      "city": user['city'],
                      # "state": "AL",
                      "countryCode": "PL",
                      "email": user['email'],#"8awgqyk6a5+cub31c122@allegrogroup.pl",
                      "phone": user['phone'], #"+48500600700",
                    },
                    "referenceNumber": delivery_name[:30], #"Allegro Odbior w Punkcie UPS", 
                    "description": description,
                    "packages": [
                      {
                        "type": packageTypes, #"PACKAGE",
                        "length": {
                          "value": length_value,
                          "unit": "CENTIMETER"
                        },
                        "width": {
                          "value": width_value,
                          "unit": "CENTIMETER"
                        },
                        "height": {
                          "value": height_value,
                          "unit": "CENTIMETER"
                        },
                        "weight": {
                          "value": weight_value,
                          "unit": "KILOGRAMS"
                        }
                      }
                    ],
                    "insurance": {
                      "amount": "23.47",
                      "currency": "PLN"
                    },
                  #   "cashOnDelivery": {
                  #     "amount": "2.50",
                  #     "currency": "PLN",
                  #     "ownerName": "Jan Kowalski",
                  #     "iban": "PL48109024022441789739167589"
                  #   },
                    "labelFormat": "PDF",
                  #   "additionalServices": [
                  #     "ADDITIONAL_HANDLING"
                  #   ],
                  #   "additionalProperties": {
                  #     "property1": "string",
                  #     "property2": "string"
                  #   }
                  }
              }
      # if credentialsId is not None:
      #     payload["input"]["credentialsId"] = credentialsId
      response = await client.post(url, headers=headers, json=payload)
      result = response.json()
      print(' ######################### HELLO FROM UTILS PICKUP_POINT ######################### ', json.dumps(result, indent=4)) #json.dumps(result, indent=4)
    return response.json()




# =====================================================================================================================================================================================



async def cash_no_point_order(secret, order_data, external_id, offer_name, descr, user, packageTypes):

    """ Courier (cash) with pick up from seller """

    print(' ######################### cash_no_point_order external_id ######################### ', external_id)

    description = external_id
    if len(external_id) > 20:
        description = ''
    length_value = descr[0]
    if descr[0] == '':
        length_value = 20
    width_value = descr[1]
    if descr[1] == '':
        width_value = 20
    height_value = descr[2]
    # if descr[2] == '':
    #     height_value = 5
    # if descr[3] != '':
    #     weight_value = math.ceil(float(descr[3]))
    # else:
    #     weight_value = 1
    if descr[2] == '':
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            height_value = 2
        else:
          height_value = 5
    if descr[3] != '':
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            weight_value = 0.5
        else:
          weight_value = math.ceil(float(descr[3]))
    else:
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            weight_value = 0.5
        else:
          weight_value = 1

    delivery_name = order_data["delivery"]["method"]["name"] 
    delivery_name = delivery_name.replace('ł', 'l').replace('ó', 'o').replace('ż', 'z').replace(',', '').replace('.', ' ')

    async with httpx.AsyncClient() as client:
      url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/shipments/create-commands"
      headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
      payload = {
                  # "commandId": "",
                  "input": {
                    "deliveryMethodId": order_data["delivery"]["method"]["id"],
                     "sender": {
                      "name": f"{user['firstName']} {user['lastName']}",
                      "company": user['company'],
                      "street": user['street'],
                      "streetNumber": user['streetNumber'],
                      "postalCode": user['postalCode'], #"52-340"(kod Wrocław),
                      "city": user['city'],
                      # "state": "AL",
                      "countryCode": "PL",
                      "email": user['email'],#"8awgqyk6a5+cub31c122@allegrogroup.pl",
                      "phone": user['phone'], #"+48500600700",
                    },
                    "receiver": {
                      "name": "Jan Kowalski", #order_data["buyer"]["firstName"],
                      "company": order_data["buyer"]["companyName"],
                      "street": order_data["buyer"]["address"]["street"].split()[0],
                      "streetNumber": order_data["buyer"]["address"]["street"].split()[1],
                      "postalCode": order_data["buyer"]["address"]["postCode"],
                      "city": order_data["buyer"]["address"]["city"],
                      # "state": "AL",
                      "countryCode": order_data["buyer"]["address"]["countryCode"],
                      "email": order_data["buyer"]["email"],
                      "phone": "+48500600700", #order_data["delivery"]["address"]["phoneNumber"],
                    },
                    "pickup": {
                      "name": f"{user['firstName']} {user['lastName']}",
                      "company": user['company'],
                      "street": user['street'],
                      "streetNumber": user['streetNumber'],
                      "postalCode": user['postalCode'], #"52-340"(kod Wrocław),
                      "city": user['city'],
                      # "state": "AL",
                      "countryCode": "PL",
                      "email": user['email'],#"8awgqyk6a5+cub31c122@allegrogroup.pl",
                      "phone": user['phone'], #"+48500600700",
                    },
                    "referenceNumber": delivery_name[:30],
                    "description": description,
                    "packages": [
                      {
                        "type": packageTypes, #"PACKAGE",
                        "length": {
                          "value": length_value,
                          "unit": "CENTIMETER"
                        },
                        "width": {
                          "value": width_value,
                          "unit": "CENTIMETER"
                        },
                        "height": {
                          "value": height_value,
                          "unit": "CENTIMETER"
                        },
                        "weight": {
                          "value": weight_value,
                          "unit": "KILOGRAMS"
                        }
                      }
                    ],
                    "insurance": {
                      "amount": "23.47",
                      "currency": "PLN"
                    },
                    "cashOnDelivery": {
                      "amount": order_data["summary"]['totalToPay']['amount'],
                      "currency": order_data["summary"]['totalToPay']['currency'],
                      "ownerName": "Jan Kowalski",
                      "iban": "PL71 1140 3391 6412 8208 2186 7285"
                    },
                    "labelFormat": "PDF",
                  #   "additionalServices": [
                  #     "ADDITIONAL_HANDLING"
                  #   ],
                  #   "additionalProperties": {
                  #     "property1": "string",
                  #     "property2": "string"
                  #   }
                  }
              }

      response = await client.post(url, headers=headers, json=payload)
      # result = response.json()
      print(' ######################### HELLO FROM UTILS CASH COURIER WITHOUT PICKUP_POINT ######################### ') #json.dumps(result, indent=4)
    return response.json()




# =====================================================================================================================================================================================




async def no_pickup_point_order(secret, order_data, external_id, offer_name, descr, user, packageTypes):
    
    """ With courier pickup from seller & without client point(to home) """
    
    # print(' ######################### pickup_point_order secret ######################### ', secret.access_token)
    # print(' ######################### pickup_point_order order_data ######################### ', order_data["delivery"]["pickupPoint"]) 
    print(' ######################### no_pickup_point_order external_id ######################### ', external_id)
    print(' ######################### no_pickup_point_order delivery method id ######################### ', order_data["delivery"]["method"]["id"])
    # print(' ######################### no_pickup_point_order phoneNumber ######################### ', order_data["delivery"]["address"]["phoneNumber"])
    print(' ######################### no_pickup_point_order descr [3] ######################### ', descr[3])
    print(' ######################### no_pickup_point_order descr ######################### ', descr)
    print(' ######################### no_pickup_point_order order_data ######################### ', order_data)

    pickupPointId = order_data["delivery"]["pickupPoint"]
    if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka" or \
      order_data["delivery"]["method"]["name"] == "Allegro Przesyłka polecona":
        pickupPointId = '995721'
    

    description = external_id
    if len(external_id) > 20:
        description = ''
    length_value = descr[0]
    if descr[0] == '':
        length_value = 20
    width_value = descr[1]
    if descr[1] == '':
        width_value = 20
    height_value = descr[2]
    if descr[2] == '':
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            height_value = 2
        else:
          height_value = 5
    if descr[3] != '':
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            weight_value = 0.5
        else:
          weight_value = math.ceil(float(descr[3]))
    else:
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            weight_value = 0.5
        else:
          weight_value = 1

    delivery_name = order_data["delivery"]["method"]["name"] 
    delivery_name = delivery_name.replace('ł', 'l').replace('ó', 'o').replace('ż', 'z').replace(',', '').replace('.', ' ')
    
    """ Courier with pick up from seller """
    async with httpx.AsyncClient() as client:
      url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/shipments/create-commands"
      headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
      payload = {
                  # "commandId": "",
                  "input": {
                    "deliveryMethodId": order_data["delivery"]["method"]["id"],
                    "sender": {
                      "name": f"{user['firstName']} {user['lastName']}",
                      "company": user['company'],
                      "street": user['street'],
                      "streetNumber": user['streetNumber'],
                      "postalCode": user['postalCode'], #"52-340"(kod Wrocław),
                      "city": user['city'],
                      # "state": "AL",
                      "countryCode": "PL",
                      "email": user['email'],#"8awgqyk6a5+cub31c122@allegrogroup.pl",
                      "phone": "+48500600700", #user['phone'],
                    },
                    "receiver": {
                      "name": "Jan Kowalski", #order_data["buyer"]["firstName"],
                      "company": order_data["buyer"]["companyName"],
                      "street": order_data["buyer"]["address"]["street"].split()[0],
                      "streetNumber": order_data["buyer"]["address"]["street"].split()[1],
                      "postalCode": order_data["buyer"]["address"]["postCode"],
                      "city": order_data["buyer"]["address"]["city"],
                      # "state": "AL",
                      "countryCode": order_data["buyer"]["address"]["countryCode"],
                      "email": order_data["buyer"]["email"],
                      "phone": order_data["delivery"]["address"]["phoneNumber"],
                      # "point": order_data["delivery"]["pickupPoint"]["id"]
                    },
                    "pickup": {
                      "name": f"{user['firstName']} {user['lastName']}",
                      "company": user['company'],
                      "street": user['street'],
                      "streetNumber": user['streetNumber'],
                      "postalCode": user['postalCode'], #"52-340"(kod Wrocław),
                      "city": user['city'],
                      # "state": "AL",
                      "countryCode": "PL",
                      "email": user['email'],#"8awgqyk6a5+cub31c122@allegrogroup.pl",
                      "phone": user['phone'],
                      "point": pickupPointId, #"995721", #(Poczta Polska Warszawa)
                    },
                    "referenceNumber": delivery_name[:30],
                    "description": description,
                    "packages": [
                      {
                        "type": packageTypes, #"PACKAGE",
                        "length": {
                          "value": 2, #length_value,
                          "unit": "CENTIMETER"
                        },
                        "width": {
                          "value": 32, #width_value,
                          "unit": "CENTIMETER"
                        },
                        "height": {
                          "value": 23, #height_value,
                          "unit": "CENTIMETER"
                        },
                        "weight": {
                          "value": weight_value,
                          "unit": "KILOGRAMS"
                        }
                      }
                    ],
                    "insurance": {
                      "amount": "23.47",
                      "currency": "PLN"
                    },
                  #   "cashOnDelivery": {
                  #     "amount": "2.50",
                  #     "currency": "PLN",
                  #     "ownerName": "Jan Kowalski",
                  #     "iban": "PL48109024022441789739167589"
                  #   },
                    "labelFormat": "PDF",
                  #   "additionalServices": [
                  #     "ADDITIONAL_HANDLING"
                  #   ],
                  #   "additionalProperties": {
                  #     "property1": "string",
                  #     "property2": "string"
                  #   }
                  }
              }
      # if credentialsId is not None:
      #     payload["input"]["credentialsId"] = credentialsId
      response = await client.post(url, headers=headers, json=payload)
      result = response.json()
      print(' ######################### COURIER WITH PICKUP FROM SELLER ######################### ', json.dumps(result, indent=4)) #credentialsId #json.dumps(result, indent=4)
    return response.json()




# =====================================================================================================================================================================================


# ---@#$ NIE UŻYWANA FUNKCJA

def nie_pickup_point_order(secret, order_data, external_id, offer_name, descr, credentialsId, packageTypes):
    
    """ Courier without pick up from seller """

    print(' ######################### nie_pickup_point_order external_id ######################### ', external_id)

    if descr[0] == '':
        length_value = 20
    if descr[1] == '':
        width_value = 20
    if descr[2] == '':
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            height_value = 2
        else:
          height_value = 5
    if descr[3] != '':
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            weight_value = 0.5
        else:
          weight_value = math.ceil(float(descr[3]))
    else:
        if order_data["delivery"]["method"]["name"] == "Allegro MiniPrzesyłka":
            weight_value = 0.5
        else:
          weight_value = 1

    delivery_name = order_data["delivery"]["method"]["name"] 
    [item.replace('ł', 'l').replace('ó', 'o').replace(',', '') for item in delivery_name]

    url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/shipments/create-commands"
    headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
    payload = {
                # "commandId": "",
                "input": {
                  "deliveryMethodId": order_data["delivery"]["method"]["id"],
                  "sender": {
                    "name": "Jan Kowalski",
                    "company": "Allegro.pl sp. z o.o.",
                    "street": "Główna",
                    "streetNumber": "30",
                    "postalCode": "64-700",
                    "city": "Warszawa",
                    # "state": "AL",
                    "countryCode": "PL",
                    "email": "8awgqyk6a5+cub31c122@allegrogroup.pl",
                    "phone": "+48500600700",
                    # "point": ""
                  },
                  "receiver": {
                    "name": "Jan Kowalski", #order_data["buyer"]["firstName"],
                    "company": order_data["buyer"]["companyName"],
                    "street": order_data["buyer"]["address"]["street"].split()[0],
                    "streetNumber": order_data["buyer"]["address"]["street"].split()[1],
                    "postalCode": order_data["buyer"]["address"]["postCode"],
                    "city": order_data["buyer"]["address"]["city"],
                    # "state": "AL",
                    "countryCode": order_data["buyer"]["address"]["countryCode"],
                    "email": order_data["buyer"]["email"],
                    "phone": "+48500600700", #order_data["delivery"]["address"]["phoneNumber"],
                  },
                  "pickup": { # Niewymagane, dane miejsca odbioru przesyłki
                    "name": "Jan Kowalski",
                    "company": "Allegro.pl sp. z o.o.",
                    "street": "Główna",
                    "streetNumber": 30,
                    "postalCode": "64-700",
                    "city": "Warszawa",
                    # "state": "AL",
                    "countryCode": "PL",
                    "email": "8awgqyk6a5+cub31c122@allegromail.pl",
                    "phone": "+48500600700",
                    # "point": "A1234567"
                  },
                  "referenceNumber": delivery_name[:30],
                  "description": external_id,
                  "packages": [
                    {
                      "type": packageTypes, #"PACKAGE",
                      "length": {
                        "value": length_value,
                        "unit": "CENTIMETER"
                      },
                      "width": {
                        "value": width_value,
                        "unit": "CENTIMETER"
                      },
                      "height": {
                        "value": height_value,
                        "unit": "CENTIMETER"
                      },
                      "weight": {
                        "value": weight_value,
                        "unit": "KILOGRAMS"
                      }
                    }
                  ],
                  "insurance": {
                    "amount": "23.47",
                    "currency": "PLN"
                  },
                #   "cashOnDelivery": {
                #     "amount": "2.50",
                #     "currency": "PLN",
                #     "ownerName": "Jan Kowalski",
                #     "iban": "PL48109024022441789739167589"
                #   },
                  "labelFormat": "PDF",
                #   "additionalServices": [
                #     "ADDITIONAL_HANDLING"
                #   ],
                #   "additionalProperties": {
                #     "property1": "string",
                #     "property2": "string"
                #   }
                }
            }

    response = requests.post(url, headers=headers, json=payload)
    print(' ######################### HELLO FROM UTILS COURIER WITHOUT PICKUP_POINT ######################### ')
    return response.json()