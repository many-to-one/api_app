import time, os, io, json, asyncio, httpx, requests
from django.conf import settings
from django.shortcuts import render

from celery import shared_task
from ..views_folder.orders_views_test import *

from django.core.handlers.asgi import ASGIRequest
from io import BytesIO



def create_request(query_string, path='/'):

    scope = {
        'type': 'http',
        'http_version': '1.1',
        'method': 'GET',
        'path': path,
        'raw_path': path.encode('utf-8'),
        'query_string': query_string.encode('utf-8'),
        'headers': [],
    }

    async def receive():
        return {'type': 'http.request', 'body': b''}

    req = ASGIRequest(scope, receive)
    return req


@shared_task
def invoice_task(results, secret, name):
    print('######### CELERY seller ###########', results)
    return results


def get_user(secret):

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/me" 
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-type': "application/vnd.allegro.public.v1+json"} 
        response = requests.get(url, headers=headers)
        result = response.json()
        return  result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)



@shared_task
def get_invoice_task(query_string, results, secret, name, seller):

    request = create_request(query_string)

    tasks_ = []

    for res in results:
        print('@@@@@@@@@@@@@ RES  @@@@@@@@@@@@@', res)
        if isinstance(res, (list)):
            print('@@@@@@@@@@@@@ RES TUPLE @@@@@@@@@@@@@', res)
            tasks = []
            for i in res:
                print('@@@@@@@@@@@@@ I I I  @@@@@@@@@@@@@', i)
                if isinstance(i, (dict)):
                    for key, value in i.items():
                        if key == "payment":
                            print('@@@@@@@@@@@@@ VALUE 1 @@@@@@@@@@@@@', value)
                            tasks.append(value)
                        if key == "lineItems":
                            print('@@@@@@@@@@@@@ VALUE 2 @@@@@@@@@@@@@', value)
                            tasks.append(value)
                        if key == "invoice" and value.get('required') is True:
                            print('@@@@@@@@@@@@@ VALUE 3 @@@@@@@@@@@@@', value)
                            tasks.append(value.get('address')) 
            # print('@@@@@@@@@@@@@ TASKS @@@@@@@@@@@@@', tasks)

            tasks_.append(invoice_template(request, seller, tasks, secret))
            time.sleep(2)
    # invoice_template(request, seller, tasks, secret)

    # get_test(request, seller, tasks, secret)
    # invoices = [
    #     print('********************** get_invoice value ****************************', value.get('address')) 
    #     # tasks.append(value.get('address'))
    #     for i in res[0] 
    #     if isinstance(i, (dict))
    #     for key, value in i.items()
    #     if key == "invoice"
    #     if value.get('required') is True
    # ]

    # seller = await asyncio.gather(get_user(name, secret))
    # invoice_result = await asyncio.gather(*tasks_)  
    # invoice_result = asyncio.run(*tasks_) 
    print('@@@@@@@@@@@@@ TASKS @@@@@@@@@@@@@', secret)   
    return tasks_ #invoice_template(request, seller, tasks, secret)   
    # return seller, tasks_


def get_test(request, seller, tasks, secret):
    print('$$$$$$$$$$$$$$$$$ TESTS TESTS $$$$$$$$$$$$$$$$$$$$$$', seller, tasks, secret)
    return tasks

def invoice_template(request, seller, invoice, secret):
    print('******************* invoice_template ******************',seller, invoice)

    #iterate invoice!!!
    # for invoice in invoices:
    print('&&&&&&&&&&&&&&&&&&& invoice &&&&&&&&&&&&&&&&&&&&', invoice)
    context = {
            'seller': seller[0],  
            'payment': invoice[0],
            'customer': invoice[1],  
            'order': invoice[2],  
        }
        
    print('&&&&&&&&&&&&&&&&&&& LOGIN &&&&&&&&&&&&&&&&&&&&', seller[0]["login"])
        
    pdf, size = html_to_pdf('invoice_template.html', context)
    # pdf_base64 = base64.b64encode(pdf).decode("utf-8")
    if pdf:
        attachment_id = get_attachment_id(request, pdf, size, secret)
        print('&&&&&&&&&&&&&&&&&&& pdf &&&&&&&&&&&&&&&&&&&&', pdf)
        print('&&&&&&&&&&&&&&&&&&& attachment_id &&&&&&&&&&&&&&&&&&&&', attachment_id["id"])
        
    if attachment_id:
        url = f"https://api.allegro.pl.allegrosandbox.pl/messaging/messages"
        headers = {'Authorization': f'Bearer {secret["access_token"]}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-Type': "application/vnd.allegro.public.v1+json"}

        data = {
            "recipient": {
                "login": "alfapro" #seller[0]["login"]
            },
            "text": "tests-7",
            "attachments": [
                {"id": attachment_id["id"]}
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if 'error' in result:
            pass
                            
        print('@@@@@@@@@ INVOICE @@@@@@@@@', json.dumps(result, indent=4))
        print('@@@@@@@@@ INVOICE HEADERS @@@@@@@@@', response.headers)


def get_attachment_id(request, pdf_base64, size, secret):
    # print('******************* invoice_template ******************',seller, invoce)
    
    url = f"https://api.allegro.pl.allegrosandbox.pl/messaging/message-attachments"  #messaging/messages"
    headers = {'Authorization': f'Bearer {secret["access_token"]}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-Type': "application/vnd.allegro.public.v1+json"}

    data = {
        "filename": pdf_base64,
        "size": size
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if 'error' in result:
        pass
                    
    print('@@@@@@@@@ ATTACHMENT_ID @@@@@@@@@', json.dumps(result, indent=4))

    return result


from django.http import HttpResponse
from django.views.generic import View
from django.template.loader import get_template
from xhtml2pdf import pisa
def html_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-2")), result)

    pdf_file_path = os.path.join(settings.BASE_DIR, 'invoices', 'myfile.pdf')
    # Ensure the directory exists
    os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)

    if not pdf.err:
        with open(pdf_file_path, "wb") as pdf_file:
            pdf_file.write(result.getvalue())
        pdf_size = result.tell()
        # return HttpResponse(result.getvalue(), content_type='application/pdf')
        return pdf_file_path, pdf_size
    # return None







# @shared_task
# async def get_invoice_task(request, results, secret, name):

#     tasks_ = []

#     seller = await asyncio.gather(get_user(name, secret))

#     for res in results:
#         if isinstance(res, (tuple)):
#             tasks = []
#             for i in res:
#                 if isinstance(i, (dict)):
#                     for key, value in i.items():
#                         if key == "payment":
#                             tasks.append(value)
#                         if key == "lineItems":
#                             tasks.append(value)
#                         if key == "invoice" and value.get('required') is True:
#                             tasks.append(value.get('address')) 
#             # print('@@@@@@@@@@@@@ TASKS @@@@@@@@@@@@@', tasks)
#             invoice_result = await asyncio.gather(
#                 invoice_template(request, seller, tasks, secret)
#             )
#             tasks_.append(invoice_result)

#             # invoices = [
#             #     print('********************** get_invoice value ****************************', value.get('address')) 
#             #     # tasks.append(value.get('address'))
#             #     for i in res[0] 
#             #     if isinstance(i, (dict))
#             #     for key, value in i.items()
#             #     if key == "invoice"
#             #     if value.get('required') is True
#             # ]

#     # seller = await asyncio.gather(get_user(name, secret))
#     # invoice_result = await asyncio.gather(*tasks_)
#     print('@@@@@@@@@@@@@ TASKS_ @@@@@@@@@@@@@', tasks_)
        
#     return seller, tasks_


# async def invoice_template(request, seller, invoice, secret):
#     print('******************* invoice_template ******************',seller, invoice)

#     #iterate invoice!!!
#     # for invoice in invoices:
#     print('&&&&&&&&&&&&&&&&&&& invoice &&&&&&&&&&&&&&&&&&&&', invoice)
#     context = {
#             'seller': seller[0],  
#             'payment': invoice[0],
#             'customer': invoice[1],  
#             'order': invoice[2],  
#         }
        
#     print('&&&&&&&&&&&&&&&&&&& LOGIN &&&&&&&&&&&&&&&&&&&&', seller[0]["login"])
        
#     pdf, size = await html_to_pdf('invoice_template.html', context)
#     # pdf_base64 = base64.b64encode(pdf).decode("utf-8")
#     attachment_id = await get_attachment_id(request, pdf, size, secret)
#     print('&&&&&&&&&&&&&&&&&&& pdf &&&&&&&&&&&&&&&&&&&&', pdf)
        
#     if attachment_id:
#         async with httpx.AsyncClient() as client:
#             url = f"https://api.allegro.pl.allegrosandbox.pl/messaging/messages"
#             headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-Type': "application/vnd.allegro.public.v1+json"}

#             data = {
#                 "recipient": {
#                     "login": "alfapro" #seller[0]["login"]
#                 },
#                 "text": "tests-2",
#                 "attachments": [
#                     # {"id": attachment_id}
#                 ]
#             }

#             response = await client.post(url, headers=headers, json=data)
#             result = response.json()

#             if 'error' in result:
#                 error_code = result['error']
#                 if error_code == 'invalid_token':
#                     # print('ERROR RESULT @@@@@@@@@', error_code)
#                     try:
#                         # Refresh the token
#                         new_token = get_next_token(request, secret.refresh_token, 'retset')
#                         # Retry fetching orders with the new token
#                         return get_order_details(request, id)
#                     except Exception as e:
#                         print('Exception @@@@@@@@@', e)
#                         context = {'name': 'retset'}
#                         return render(request, 'invalid_token.html', context)
                            
#             print('@@@@@@@@@ INVOICE @@@@@@@@@', json.dumps(result, indent=4))


# async def get_attachment_id(request, pdf_base64, size, secret):
#     # print('******************* invoice_template ******************',seller, invoce)
    
#     async with httpx.AsyncClient() as client:
#         url = f"https://api.allegro.pl.allegrosandbox.pl/messaging/message-attachments"  #messaging/messages"
#         headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-Type': "application/vnd.allegro.public.v1+json"}

#         data = {
#             "filename": pdf_base64,
#             "size": size
#         }

#         response = await client.post(url, headers=headers, json=data)
#         result = response.json()

#         if 'error' in result:
#             error_code = result['error']
#             if error_code == 'invalid_token':
#                 # print('ERROR RESULT @@@@@@@@@', error_code)
#                 try:
#                     # Refresh the token
#                     new_token = get_next_token(request, secret.refresh_token, 'retset')
#                     # Retry fetching orders with the new token
#                     return get_order_details(request, id)
#                 except Exception as e:
#                     print('Exception @@@@@@@@@', e)
#                     context = {'name': 'retset'}
#                     return render(request, 'invalid_token.html', context)
                    
#         print('@@@@@@@@@ ATTACHMENT_ID @@@@@@@@@', json.dumps(result, indent=4))

#     return result


# from django.http import HttpResponse
# from django.views.generic import View
# from django.template.loader import get_template
# from xhtml2pdf import pisa
# async def html_to_pdf(template_src, context_dict={}):
#     template = get_template(template_src)
#     html = template.render(context_dict)
#     result = io.BytesIO()
#     pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-2")), result)

#     pdf_file_path = os.path.join(settings.BASE_DIR, 'invoices', 'myfile.pdf')
#     # Ensure the directory exists
#     os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)

#     if not pdf.err:
#         with open("invoice.pdf", "wb") as pdf_file:
#             pdf_file.write(result.getvalue())
#         pdf_size = result.tell()
#         # return HttpResponse(result.getvalue(), content_type='application/pdf')
#         return "invoice.pdf", pdf_size
#     # return None