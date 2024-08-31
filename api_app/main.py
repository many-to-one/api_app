import base64
import hashlib
import secrets
import string
import requests
import json

CLIENT_ID = "73b22f6b7a47415598faf4b57c2f0f45"          # wprowadź Client_ID aplikacji
CLIENT_SECRET = "RQf9EiQVweReagQD7Ob2BKoKGwHX8hTndVB4pLSKOOeuVpVRnFjWOJtDepzlf51H"      # wprowadź Client_Secret aplikacji
REDIRECT_URI = "http://127.0.0.1:8000/"       # wprowadź redirect_uri
AUTH_URL = "https://allegro.pl.allegrosandbox.pl/auth/oauth/authorize"
TOKEN_URL = "https://allegro.pl.allegrosandbox.pl/auth/oauth/token"


def generate_code_verifier():
    code_verifier = ''.join((secrets.choice(string.ascii_letters) for i in range(40)))
    return code_verifier


def generate_code_challenge(code_verifier):
    hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    base64_encoded = base64.urlsafe_b64encode(hashed).decode('utf-8')
    code_challenge = base64_encoded.replace('=', '')
    return code_challenge


def get_authorization_code(code_verifier):
    code_challenge = generate_code_challenge(code_verifier)
    authorization_redirect_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}" \
                                 f"&code_challenge_method=S256&code_challenge={code_challenge}"
    print("Zaloguj do Allegro - skorzystaj z url w swojej przeglądarce oraz wprowadź authorization code ze zwróconego url: ")
    print(f"--- {authorization_redirect_url} ---")
    authorization_code = input('code: ')
    return authorization_code


def get_access_token(authorization_code, code_verifier):
    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code,
                'redirect_uri': REDIRECT_URI, 'code_verifier': code_verifier}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=False)
        response_body = json.loads(access_token_response.text)
        return response_body
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


#################################################################################################################################
################################################## ASYNCHRONUS TESTS ############################################################
#################################################################################################################################

import time

def func_1(value):
    time.sleep(1)
    return f'result of func_1: {value}'

def func_2(value):
    time.sleep(1)
    return f'result of func_2: {value}'

def func_3(value):
    time.sleep(1)
    return f'result of func_3: {value}'

def synchr():
    start_time = time.time()  # Record the start time
    result_arr = []
    arr = ['value_1', 'value_2', 'value_3', 'value_4']

    for i in arr:
        res_1 = func_1(i)  # Call synchronous function
        # res_2 = func_2(i)  # Changed from func_1 to func_2
        # res_3 = func_3(i)  # Changed from func_1 to func_3
        result_arr.append(res_1)  # Removed unnecessary parentheses
    
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time

    print(f'SYNCHRONOUS RESULT - {result_arr}')
    print(f"Elapsed time: {elapsed_time} seconds")


# -------------------------------------------------------------------------------- #


import asyncio
import time

async def func_1(value):
    await asyncio.sleep(1)  # Simulate an asynchronous operation
    return f'result of func_1: {value}'

async def func_2(value):
    await asyncio.sleep(1)
    return f'result of func_2: {value}'

async def func_3(value):
    await asyncio.sleep(1)
    return f'result of func_3: {value}'

async def asynchr():
    start_time = time.time()
    result_arr = []
    arr = ['value_1', 'value_2', 'value_3', 'value_4']

    tasks = []
    for i in arr:
        tasks.append(asyncio.create_task(func_1(i)))
        # tasks.append(asyncio.create_task(func_2(i)))
        # tasks.append(asyncio.create_task(func_3(i)))

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)

    # Group the results in threes
    for i in range(0, len(results), 3):
        result_arr.append((results[i])) #results[i+1], results[i+2]
    
    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f'ASYNCHRONOUS RESULT - {result_arr}')
    print(f"Elapsed time: {elapsed_time} seconds")



def make_order():

    token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiIxMDY5MzA1OTAiLCJzY29wZSI6WyJhbGxlZ3JvOmFwaTpvcmRlcnM6cmVhZCIsImFsbGVncm86YXBpOmZ1bGZpbGxtZW50OnJlYWQiLCJhbGxlZ3JvOmFwaTpwcm9maWxlOndyaXRlIiwiYWxsZWdybzphcGk6c2FsZTpvZmZlcnM6d3JpdGUiLCJhbGxlZ3JvOmFwaTpmdWxmaWxsbWVudDp3cml0ZSIsImFsbGVncm86YXBpOmJpbGxpbmc6cmVhZCIsImFsbGVncm86YXBpOmNhbXBhaWducyIsImFsbGVncm86YXBpOmRpc3B1dGVzIiwiYWxsZWdybzphcGk6c2FsZTpvZmZlcnM6cmVhZCIsImFsbGVncm86YXBpOnNoaXBtZW50czp3cml0ZSIsImFsbGVncm86YXBpOmJpZHMiLCJhbGxlZ3JvOmFwaTpvcmRlcnM6d3JpdGUiLCJhbGxlZ3JvOmFwaTphZHMiLCJhbGxlZ3JvOmFwaTpwYXltZW50czp3cml0ZSIsImFsbGVncm86YXBpOnNhbGU6c2V0dGluZ3M6d3JpdGUiLCJhbGxlZ3JvOmFwaTpwcm9maWxlOnJlYWQiLCJhbGxlZ3JvOmFwaTpyYXRpbmdzIiwiYWxsZWdybzphcGk6c2FsZTpzZXR0aW5nczpyZWFkIiwiYWxsZWdybzphcGk6cGF5bWVudHM6cmVhZCIsImFsbGVncm86YXBpOnNoaXBtZW50czpyZWFkIiwiYWxsZWdybzphcGk6bWVzc2FnaW5nIl0sImFsbGVncm9fYXBpIjp0cnVlLCJpc3MiOiJodHRwczovL2FsbGVncm8ucGwuYWxsZWdyb3NhbmRib3gucGwiLCJleHAiOjE3MjUxNDU0OTAsImp0aSI6IjhlMWU2ZjgwLTEzZDgtNDhkOC05Nzk2LWRkNjA0NjJjMjdjYyIsImNsaWVudF9pZCI6IjczYjIyZjZiN2E0NzQxNTU5OGZhZjRiNTdjMmYwZjQ1In0.MogjhXsQaToa_ZjEmUdAZ73RX7NOgzaSR6xa2hEdNuQDuSY_rEQu3qZHR2JbtfP_MA3nFkeNQu4_wj7LsFRSmF1sb55fprbxXzet-veAK24zDbhh3fofyLweaMIkft-8rN_LyKF_DL8Uih5YSCPldpC9RQ5tcsKRmxDB4A6fk054HPfw4FoQ7CAw5WWeiYJ0NzPBu_mqruTbHhpO8AQcUEnla_7MSbFGwAV_RLqRIp043ZJ1rITolvBn9p_PE6MAjtnEZIYDanDvtiJDY5hyeHM6KNiUFZJjIjLC-P03YUdkm8Dvo_XSltu6dQsvmhwejfrv6RZ_9eBIY67eMRQx75FRW8uM1xUpIqfR6HZZCsTZUoMuHVKbdG2Th3OewybH4Vc65jkMw72MwVhyJyrjsxvQFlcLuIt03Za0JECAXWbrevznHRq-NwJP512F_2wwRe5zIKw3CwCHjNxUG2KnhUsYPp4-p7iS4Lt2hvjWZEhWEbEDPeVfMwFvAE6RlcNP1c8iBM8qChOIVgASLFx2Z3tH52zrxAgmn1IOXK1GQcc0Dn0RT9hvZRaH1YRJDII0RqdlGYELYCmz6iZiDqZgl3sRCSLZHB3sGGsWdJVcYUxvkHFFtpvcSSKtwb2sxf-PgTtvxBrZdwiAlti-eWlnA5mddtZtbRs2eyR_bRhw-Z4'
    commandId = 'b1434ef9-2e77-4017-b71a-84c372650cde'

    # url = f"https://api.allegro.pl.allegrosandbox.pl/shipment-management/shipments/create-commands/{commandId}"
    url = f"https://api.allegro.pl.allegrosandbox.pl/parcel-management/parcel-create-commands/{commandId}"
    headers = {'Authorization': f'Bearer {token}', 'Accept': "application/vnd.allegro.public.v1+json"} 

    response = requests.get(url, headers=headers)
    result = response.json()


    print('@@@@@@@@@ MAKE ORDER RESULT @@@@@@@@@', json.dumps(result, indent=4))
    print('@@@@@@@@@ MAKE ORDER HEADERS @@@@@@@@@', response.headers)
    # print('@@@@@@@@@ MAKE ORDER VALIDATION_ERROR @@@@@@@@@', result['errors'][0]["code"])
        



def main():
    make_order()
    # synchr()
    # asyncio.run(asynchr())


    # code_verifier = generate_code_verifier()
    # authorization_code = get_authorization_code(code_verifier)
    # response = get_access_token(authorization_code, code_verifier)
    # access_token = response['access_token']
    # print(f"access token = {access_token}")




if __name__ == "__main__":
    main()