import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from ..models import *
from ..utils import *


def all_messages(request, name):

    # print('******* name ********', name)
    account = Allegro.objects.get(name=name)
    # print('******* account ********', account)
    secret = Secret.objects.get(account=account)
    # print('******* secret ********', secret)
    # print('******* secret.access_token ********', secret.access_token)

    try:
        url = "https://api.allegro.pl.allegrosandbox.pl/messaging/threads" 
        # headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        mess_result = requests.get(url, headers=headers, verify=True)
        result = mess_result.json()
        print('******* product_result ********', result)
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token, name)
                    # Retry fetching orders with the new token
                    return all_messages(request, name)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    context = {'name': name}
                    return render(request, 'invalid_token.html', context)
        # print('RESULT - all_messages - @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': mess_result.json(),
            'name': name,
        }
        return render(request, 'all_messages.html', context)
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    # return HttpResponse ('Ok')


def get_one_message(request):

    data = json.loads(request.body.decode('utf-8'))
    name = data.get('name')
    threadId = data.get('threadId')

    print('************** name **************', name)
    print('************** threadId **************', threadId)

    account = Allegro.objects.get(name=name)
    secret = Secret.objects.get(account=account)
    
    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/messaging/threads/{threadId}/messages/"
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
                    return get_one_message(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    return redirect('invalid_token')
        print('RESULT - get_one_message - @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'result': product_result.json()
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


def send_message(request):

    try:
        data = json.loads(request.body.decode('utf-8'))
        content = data.get('content')
        threadId = data.get('threadId')

        print('************** SEND MESSAGE **************')
        print('************** content **************', content)
        print('************** threadId **************', threadId)

        return JsonResponse({'message': 'Gotowe!'}, status=200)
    except:
        # Return a JSON response with an error message
        return JsonResponse({'error': 'Invalid request method!'}, status=400)