import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
import requests
import os
import base64
import time
import io
import zipfile
import PyPDF2
from django.conf import settings
from dotenv import load_dotenv

from ..celery_tasks.invoices_tasks import *
load_dotenv()
from ..models import *
from ..utils import *
# from ..views_folder.offer_views import get_one_offer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import asyncio
import httpx
from asgiref.sync import sync_to_async, async_to_sync
from ..views import get_new_authorization_code, index

REDIRECT_URI = os.getenv('REDIRECT_URI')      # wprowadź redirect_uri
AUTH_URL = os.getenv('AUTH_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ENVIRONMENT = os.getenv('ENVIRONMENT')


class Offers:

    def __init__(self, name):
        self.name = name


    def credentials(self):
        secret = Secret.objects.get(account__name=self.name)
        token = secret.access_token
        refresh_token = secret.refresh_token
        name = secret.account.name

        context = {
            'token': token,
            'refresh_token': refresh_token,
            'name': name,
        }

        return context
    


    def get_(self, request, url, debug_name):

        context = self.credentials()

        try:
            headers = {
                'Authorization': f'Bearer {context["token"]}', 
                'Accept': "application/vnd.allegro.public.v1+json"
            }
            json_result = requests.get(f'{ENVIRONMENT}/{url}', headers=headers, verify=True)
            result = json_result.json()
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    try:
                        # Refresh the token and retry the request
                        # new_token = get_next_token(request, context['refresh_token'], context['name'])
                        new_token = get_new_authorization_code(request, context['name'])
                        if new_token:
                            # Retry the request with the new token
                            headers = {
                                'Authorization': f'Bearer {new_token}', 
                                'Accept': "application/vnd.allegro.public.v1+json"
                            }
                            json_result = requests.get(url, headers=headers, verify=True)
                            result = json_result.json()

                            # Update the secret with the new token
                            secret = Secret.objects.get(account__name=self.name)
                            secret.access_token = new_token
                            secret.save()
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': context['name']}
                        return render(request, 'invalid_token.html', context)
            # print(f'@@@@@@@@@ sync_get RESULT for {debug_name} @@@@@@@@@', json.dumps(result, indent=4))
            print(f'@@@@@@@@@ sync_get HEADERS for {debug_name} @@@@@@@@@', json_result.headers)

            return result
        
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        


    def post_(self, request, url, payload, debug_name):

        context = self.credentials()

        try:
            headers = {
                'Authorization': f'Bearer {context["token"]}', 
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Content-Type': 'application/vnd.allegro.public.v1+json'
            }
            json_result = requests.post(url, headers=headers, json=payload)
            result = json_result.json()
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    try:
                        # Refresh the token and retry the request
                        # new_token = get_next_token(request, context['refresh_token'], context['name'])
                        new_token = get_new_authorization_code(request, context['name'])
                        if new_token:
                            # Retry the request with the new token
                            headers = {
                                'Authorization': f'Bearer {new_token}', 
                                'Accept': "application/vnd.allegro.public.v1+json",
                                'Content-Type': 'application/vnd.allegro.public.v1+json'
                            }
                            json_result = requests.post(url, headers=headers, json=payload)
                            result = json_result.json()

                            # Update the secret with the new token
                            secret = Secret.objects.get(account__name=self.name)
                            secret.access_token = new_token
                            secret.save()
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': context['name']}
                        return render(request, 'invalid_token.html', context)
            print(f'@@@@@@@@@ sync_get RESULT for {debug_name} @@@@@@@@@', json.dumps(result, indent=4))
            print(f'@@@@@@@@@ sync_get HEADERS for {debug_name} @@@@@@@@@', json_result.headers)

            return result
        
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        


    def patch_(self, request, url, payload, debug_name):

        context = self.credentials()

        try:
            headers = {
                'Authorization': f'Bearer {context["token"]}', 
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Content-Type': 'application/vnd.allegro.public.v1+json'
            }
            json_result = requests.patch(url, headers=headers, json=payload)
            result = json_result.json()
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    try:
                        # Refresh the token and retry the request
                        # new_token = get_next_token(request, context['refresh_token'], context['name'])
                        new_token = get_new_authorization_code(request, context['name'])
                        if new_token:
                            # Retry the request with the new token
                            headers = {
                                'Authorization': f'Bearer {new_token}', 
                                'Accept': "application/vnd.allegro.public.v1+json",
                                'Content-Type': 'application/vnd.allegro.public.v1+json'
                            }
                            json_result = requests.patch(url, headers=headers, json=payload)
                            result = json_result.json()

                            # Update the secret with the new token
                            secret = Secret.objects.get(account__name=self.name)
                            secret.access_token = new_token
                            secret.save()
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': context['name']}
                        return render(request, 'invalid_token.html', context)
            print(f'@@@@@@@@@ sync_get RESULT for {debug_name} @@@@@@@@@', json.dumps(result, indent=4))
            print(f'@@@@@@@@@ sync_get HEADERS for {debug_name} @@@@@@@@@', json_result.headers)

            return result
        
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)