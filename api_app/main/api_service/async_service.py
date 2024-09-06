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
from ..views import index

REDIRECT_URI = os.getenv('REDIRECT_URI')      # wprowadź redirect_uri
AUTH_URL = os.getenv('AUTH_URL')
TOKEN_URL = os.getenv('TOKEN_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')



async def async_get(request, *args, **kwargs):

    url = kwargs.get('url')
    # print(' @@@@@@@@@ url @@@@@@@@@ ', url)
    token = kwargs.get('token')
    refresh_token = kwargs.get('refresh_token')
    name = kwargs.get('name')
    debug_name = kwargs.get('debug_name')

    try:
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {token}', 'Accept': "application/vnd.allegro.public.v1+json"}
            json_result = await client.get(url, headers=headers) #verify=True
            result = json_result.json()
            if 'error' in result:
                error_code = result['error']
                if error_code == 'invalid_token':
                    try:
                        # Get new token
                        get_next_token(request, refresh_token, name)
                        # Back to the home page
                        return index(request)
                    except Exception as e:
                        print('Exception @@@@@@@@@', e)
                        context = {'name': name}
                        return render(request, 'invalid_token.html', context)
            # print(f'@@@@@@@@@ async_get RESULT for {debug_name} @@@@@@@@@', json.dumps(result, indent=4))
            print(f'@@@@@@@@@ async_get HEADERS for {debug_name} @@@@@@@@@', json_result.headers)

            return result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    



async def async_post(request, *args, **kwargs):

    url = kwargs.get('url')
    payload = kwargs.get('payload')
    token = kwargs.get('token')
    refresh_token = kwargs.get('refresh_token')
    name = kwargs.get('name')
    debug_name = kwargs.get('debug_name')

    try:
        async with httpx.AsyncClient() as client:
            if debug_name == "get_pickup_proposals 647":
                headers = {
                    'Authorization': f'Bearer {token}', 
                    # 'Accept': "application/octet-stream", 
                    'Accept': 'application/vnd.allegro.public.v1+json',
                    'Content-type': "application/vnd.allegro.public.v1+json"
                } 
            else:
                headers = {
                        'Authorization': f'Bearer {token}', 
                        'Accept': "application/octet-stream", 
                        # 'Accept': 'application/vnd.allegro.public.v1+json',
                        'Content-type': "application/vnd.allegro.public.v1+json"
                    } 
            response = await client.post(url, headers=headers, json=payload) 
            if response == '401' :
                try:
                    # Get new token
                    get_next_token(request, refresh_token, name)
                    # Back to the home page
                    return index()
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    context = {'name': name}
                    return render(request, 'invalid_token.html', context)
            print(f'@@@@@@@@@ async_post STATUS for {debug_name} @@@@@@@@@', response)
            # print(f'@@@@@@@@@ async_post RESPONSE CONTENT for {debug_name} @@@@@@@@@', response.content)
            # print(f'@@@@@@@@@ async_post RESPONSE JSON for {debug_name} @@@@@@@@@', json.dumps(response.json(), indent=4))

            return response
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)