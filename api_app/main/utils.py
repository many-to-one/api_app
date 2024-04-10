from users.models import CustomUser
from .models import *
import requests
from django.http import JsonResponse
import json
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN_URL = os.getenv('TOKEN_URL')


def get_user(request):
    user = CustomUser.objects.get(id=request.user.id)
    return user


def get_next_token(request, access_token, name):

    print(f'@#@#@#@# get_next_token access_token #@#@#@# --------- {access_token}')
    
    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)

    try:
        data = {'grant_type': 'refresh_token', 'refresh_token': access_token, 'redirect_uri': 'http://localhost:8000/get_code'}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(secret.CLIENT_ID, secret.CLIENT_SECRET))
        # print("RESPONSE CONTENT:", access_token_response.status_code)
        tokens = json.loads(access_token_response.text)
        print(f'@#@#@#@# NEXT TOKENS #@#@#@# --------- {tokens}')
        access_token = tokens['access_token']
        if access_token:
            secret.access_token = access_token
            secret.save()
            # print(f'@#@#@#@# NEXT TOKENS #@#@#@# --------- {access_token}')
            print(' ************* NEXT TOKEN WAS CREATED ************* ')
            return access_token
    except requests.exceptions.HTTPError as err:
        # raise SystemExit(err)
        print(f'******** requests.exceptions.HTTPError ******** --------- {err}')