import asyncio
import math
import time
from users.models import CustomUser
from .models import *
import requests
from django.http import JsonResponse
import json
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN_URL = os.getenv('TOKEN_URL')
import httpx


def get_user(request):
    user = CustomUser.objects.get(id=request.user.id)
    return user


async def get_token():
    secret = Secret.objects.get(account__name='retset')
    return secret.access_token


def get_next_token(request, access_token, name):

    print(f'@#@#@#@# get_next_token access_token #@#@#@# --------- {access_token}')
    
    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)
    print(f'@#@#@#@# secret #@#@#@# --------- {secret}')

    try:
        data = {'grant_type': 'refresh_token', 'refresh_token': secret.refresh_token, 'redirect_uri': 'http://localhost:8000/get_code'}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(secret.CLIENT_ID, secret.CLIENT_SECRET))
        # print("RESPONSE CONTENT:", access_token_response.status_code)
        tokens = json.loads(access_token_response.text)
        print(f'@#@#@#@# NEXT TOKENS #@#@#@# --------- {tokens}')
        access_token = tokens['access_token']
        # refresh_token = tokens['refresh_token']
        if access_token:
            secret.access_token = access_token
            # secret.refresh_token = refresh_token
            secret.save()
            # print(f'@#@#@#@# NEXT TOKENS #@#@#@# --------- {access_token}')
            print(' ************* NEXT TOKEN WAS CREATED ************* ')
            return access_token
    except requests.exceptions.HTTPError as err:
        # raise SystemExit(err)
        print(f'******** requests.exceptions.HTTPError ******** --------- {err}')













######################################################################################################################
#################################################### CREATE ORDER ####################################################
######################################################################################################################

async def test(secret, order_data, external_id, offer_name, descr, user):
    print('********************** USER TEST ****************************', user)
    result = None
    if order_data["delivery"]["pickupPoint"] == None:
        if order_data["payment"]["type"] == 'CASH_ON_DELIVERY': 
            result = await cash_no_point_order(secret, order_data, external_id, offer_name, descr)
        else:
            result = await no_pickup_point_order(secret,  order_data, external_id, offer_name, descr)
    else:
        if order_data["payment"]["type"] == 'CASH_ON_DELIVERY': 
            result = await cash_no_point_order(secret,  order_data, external_id, offer_name, descr)
        # print('********************** pickupPoint ****************************', order_data["delivery"]["pickupPoint"])
        else:
            # result = pickup_point_order(secret,  order_data, external_id, offer_name, descr)
            result = await pickup_point_order(secret,  order_data, external_id, offer_name, descr)

    return result

async def pickup_point_order(secret, order_data, external_id, offer_name, descr):

    """ Paczkomaty z podjazdem kuriera """

    if order_data["delivery"]["method"]["name"] == "Allegro Automat DHL POP BOX":
      order_data["delivery"]["pickupPoint"]["id"] = 4591097
    if order_data["delivery"]["method"]["name"] ==  "Allegro Odbiór w Punkcie DHL":
        order_data["delivery"]["pickupPoint"]["id"] = 4509455

    # print(' ######################### pickup_point_order secret ######################### ', secret.access_token)
    # print(' ######################### pickup_point_order order_data ######################### ', order_data["delivery"]["pickupPoint"]["id"]) 
    print(' ######################### pickup_point_order external_id ######################### ', order_data["delivery"]["method"]["id"])
    print(' ######################### pickup_point_order offer_name ######################### ', order_data["delivery"]["address"]["phoneNumber"])
    # print(' ######################### pickup_point_order descr ######################### ', descr)
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
                      "name": "Jan Kowalski",
                      "company": "Allegro.pl sp. z o.o.",
                      "street": "Główna",
                      "streetNumber": "30",
                      "postalCode": '64-700', #"52-340"(kod Wrocław),
                      "city": "Warszawa",
                      # "state": "AL",
                      "countryCode": "PL",
                      "email": "8awgqyk6a5+cub31c122@allegrogroup.pl",
                      "phone": "+48500600700",
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
                      "point": order_data["delivery"]["pickupPoint"]["id"]
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
                      "phone": "500600700", #"+48500600700",
                      # "point": order_data["delivery"]["pickupPoint"]["id"]
                    },
                    "referenceNumber": external_id,
                    "description": external_id,
                    "packages": [
                      {
                        "type": "PACKAGE",
                        "length": {
                          "value": descr[0],
                          "unit": "CENTIMETER"
                        },
                        "width": {
                          "value": descr[1],
                          "unit": "CENTIMETER"
                        },
                        "height": {
                          "value": descr[2],
                          "unit": "CENTIMETER"
                        },
                        "weight": {
                          "value": math.ceil(float(descr[3])),
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
      # result = response.json()
      print(' ######################### HELLO FROM UTILS PICKUP_POINT ######################### ') #json.dumps(result, indent=4)
    return response.json()




# =====================================================================================================================================================================================



async def cash_no_point_order(secret, order_data, external_id, offer_name, descr):

    """ Courier (cash) with pick up from seller """

    # print(' ######################### cash_no_point_order secret ######################### ', secret)
    # print(' ######################### cash_no_point_order order_data ######################### ', order_data)
    # print(' ######################### cash_no_point_order external_id ######################### ', external_id)
    # print(' ######################### cash_no_point_order offer_name ######################### ', offer_name)
    # print(' ######################### cash_no_point_order descr ######################### ', descr)

    async with httpx.AsyncClient() as client:
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
                    "referenceNumber": external_id,
                    "description": external_id,
                    "packages": [
                      {
                        "type": "PACKAGE",
                        "length": {
                          "value": descr[0],
                          "unit": "CENTIMETER"
                        },
                        "width": {
                          "value": descr[1],
                          "unit": "CENTIMETER"
                        },
                        "height": {
                          "value": descr[2],
                          "unit": "CENTIMETER"
                        },
                        "weight": {
                          "value": descr[3],
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




async def no_pickup_point_order(secret, order_data, external_id, offer_name, descr):
    
    # print(' ######################### no_pickup_point_order secret ######################### ', secret)
    # print(' ######################### no_pickup_point_order order_data ######################### ', order_data)
    # print(' ######################### no_pickup_point_order external_id ######################### ', external_id)
    # print(' ######################### no_pickup_point_order offer_name ######################### ', offer_name)
    # print(' ######################### no_pickup_point_order descr ######################### ', descr)
    
    # print(' ######################### pickupPoint ++ ######################### ', order_data["delivery"]["pickupPoint"])
    
    """ Courier with pick up from seller """
    async with httpx.AsyncClient() as client:
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
                      # "point": order_data["delivery"]["pickupPoint"]["id"]
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
                    "referenceNumber": external_id,
                    "description": external_id,
                    "packages": [
                      {
                        "type": "PACKAGE",
                        "length": {
                          "value": descr[0],
                          "unit": "CENTIMETER"
                        },
                        "width": {
                          "value": descr[1],
                          "unit": "CENTIMETER"
                        },
                        "height": {
                          "value": descr[2],
                          "unit": "CENTIMETER"
                        },
                        "weight": {
                          "value": descr[3],
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


# ---@#$

def nie_pickup_point_order(secret, order_data, external_id, offer_name, descr, credentialsId):
    
    """ Courier without pick up from seller """

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
                  "referenceNumber": external_id,
                  "description": external_id,
                  "packages": [
                    {
                      "type": "PACKAGE",
                      "length": {
                        "value": descr[0],
                        "unit": "CENTIMETER"
                      },
                      "width": {
                        "value": descr[1],
                        "unit": "CENTIMETER"
                      },
                      "height": {
                        "value": descr[2],
                        "unit": "CENTIMETER"
                      },
                      "weight": {
                        "value": descr[3],
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