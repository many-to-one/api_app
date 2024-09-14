import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from ..models import *
from ..utils import *
from ..api_service import sync_service, async_service


def all_messages(request, name):

    url = "messaging/threads"
    debug_name = "all_messages 13"
    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)
    # print('RESULT - all_messages - @@@@@@@@@', json.dumps(result, indent=4))
    context = {
        'result': result,
        'name': name,
    }
    return render(request, 'messages/all_messages.html', context)


def get_one_message(request):

    data = json.loads(request.body.decode('utf-8'))
    name = data.get('name')
    threadId = data.get('threadId')

        # print('************** name **************', name)
        # print('************** threadId **************', threadId)

    url = f"messaging/threads/{threadId}/messages/"
    debug_name = "all_messages 13"
    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)

    print('************** get_one_message **************', json.dumps(result["messages"][::-1], indent=4))
        
    context = {
        'user_messages': result["messages"][::-1]
    }

    return JsonResponse(
        {
            'message': 'Stock updated successfully',
            'context': context,
        }, 
        status=200,
    )
            

def update_thread(request, threadId, name):
    url = f"messaging/threads/{threadId}/messages/"
    debug_name = "all_messages 13"
    offers = sync_service.Offers(name)
    result = offers.get_(request, url, debug_name)

    context = {
        'user_messages': result["messages"][::-1]
    }

    return context


def send_message(request):

    try:
        data = json.loads(request.body.decode('utf-8'))
        content = data.get('content')
        threadId = data.get('threadId')
        name = data.get('name')
        print('************** SEND_MESSAGE name **************', name)
        print('************** SEND_MESSAGE content **************', content)
        print('************** SEND_MESSAGE threadId **************', threadId)
        url = f"messaging/threads/{threadId}/messages"
        payload = {
            "text": f'{content}',
            "attachments": []
        }
        debug_name = "send_message 55"
        post_mess = sync_service.Offers(name)
        result = post_mess.post_(request, url, payload, debug_name)
        print('************** SEND_MESSAGE result **************', result["status_code"])
        if result["status_code"] == 201:
            return JsonResponse(update_thread(request, threadId, name), status=200)
        else:
            return JsonResponse({'message': 'Wystąpił błąd'}, status=200)
    except:
        # Return a JSON response with an error message
        return JsonResponse({'error': 'Invalid request method!'}, status=400)