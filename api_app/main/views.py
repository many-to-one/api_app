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
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

def index(request):
    if request.user.is_authenticated:
        return render(request, 'index.html')
    else:
        return render(request, 'login.html')
    
def get_code(request):
    return render(request, 'get_code.html')

def get_authorization_code(request):

    REDIRECT_URI_ =' http://localhost:8000/get_code'   

    user = get_user(request)

    authorization_redirect_url = AUTH_URL + '?response_type=code&client_id=' + user.CLIENT_ID + \
                                 '&redirect_uri=' + REDIRECT_URI_
    # print("Zaloguj do Allegro - skorzystaj z url w swojej przeglądarce oraz wprowadź authorization code ze zwróconego url: ")
    # print("---  " + authorization_redirect_url + "  ---")

    return redirect(authorization_redirect_url)
        
    
def get_access_token(request, authorization_code):
 
    user = get_user(request)
    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': 'http://localhost:8000/get_code'}
        access_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(user.CLIENT_ID, user.CLIENT_SECRET))
        print("RESPONSE CONTENT:", access_token_response.status_code)
        tokens = json.loads(access_token_response.text)
        access_token = tokens['access_token']
        if access_token:
            user.access_token = access_token
            user.save()
            print(f'@#@#@#@# tokens #@#@#@# --------- {tokens}')
            return JsonResponse({
                   'message': tokens,
               })
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)