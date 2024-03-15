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

def index(request):
    if request.user.is_authenticated:
        return render(request, 'index.html')
    else:
        return render(request, 'login.html')

def get_authorization_code(request):

    user = get_user(request)
    print('USER CLIENT ID ----------', user)

    authorization_redirect_url = AUTH_URL + '?response_type=code&client_id=' + user.CLIENT_ID + \
                                 '&redirect_uri=' + REDIRECT_URI
    print("Zaloguj do Allegro - skorzystaj z url w swojej przeglądarce oraz wprowadź authorization code ze zwróconego url: ")
    print("---  " + authorization_redirect_url + "  ---")
    if authorization_redirect_url:
        context = {'authorization_redirect_url' : authorization_redirect_url}
    # authorization_code = input('code: ')
    # return authorization_code
    return render(request, 'get_authorization_code.html', context)


def get_access_token(request):

    authorization_code = get_authorization_code(request, user)

    user = get_user(request)
    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': REDIRECT_URI}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=True,
                                              allow_redirects=True, auth=(user.CLIENT_ID, user.CLIENT_SECRET))
        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        print(f'@#@#@#@# access_token #@#@#@# --------- {access_token}')
        if access_token:
            user.access_token = access_token
            user.save()
            return JsonResponse({
                    'message': 'success',
                })
        else:
            return JsonResponse({
                    'message': 'error',
                })

    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)