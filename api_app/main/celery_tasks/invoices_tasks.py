import time, os, io, json, asyncio, httpx, requests
from django.conf import settings
from django.shortcuts import render

from celery import shared_task
from ..views_folder.orders_views_test import *

from django.core.handlers.asgi import ASGIRequest
from io import BytesIO

# celery -A api_app worker -l info

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
        # print('@@@@@@@@@@@@@ RES  @@@@@@@@@@@@@', res)
        if isinstance(res, (list)):
            # print('@@@@@@@@@@@@@ RES TUPLE @@@@@@@@@@@@@', res)
            tasks = []
            for i in res:
                # print('@@@@@@@@@@@@@ I I I  @@@@@@@@@@@@@', i)
                if isinstance(i, (dict)):
                    for key, value in i.items():
                        if key == "payment":
                            # print('@@@@@@@@@@@@@ VALUE 1 @@@@@@@@@@@@@', value)
                            tasks.append(value)
                        if key == "lineItems":
                            # print('@@@@@@@@@@@@@ VALUE 2 @@@@@@@@@@@@@', value)
                            tasks.append(value)
                        if key == "invoice" and value.get('required') is True:
                            # print('@@@@@@@@@@@@@ VALUE 3 @@@@@@@@@@@@@', value)
                            tasks.append(value.get('address')) 
                        if key == "buyer":
                            # print('@@@@@@@@@@@@@ login @@@@@@@@@@@@@', value.get('login'))
                            tasks.append(value.get('login'))
            # print('@@@@@@@@@@@@@ TASKS @@@@@@@@@@@@@', tasks)

            tasks_.append(invoice_template(request, seller, tasks, secret))
            time.sleep(2)

    # print('@@@@@@@@@@@@@ TASKS @@@@@@@@@@@@@', secret)   
    return tasks_    


def invoice_template(request, seller, invoice, secret):
    # print('******************* invoice_template ******************',seller, invoice)

    #iterate invoice!!!
    # for invoice in invoices:
    print('&&&&&&&&&&&&&&&&&&& seller &&&&&&&&&&&&&&&&&&&&', seller)
    print('&&&&&&&&&&&&&&&&&&& invoice &&&&&&&&&&&&&&&&&&&&', invoice)
    context = {
            'seller': seller,  
            'payment': invoice[0],
            'customer': invoice[1],  
            'order': invoice[2],  
        }
        
    # print('&&&&&&&&&&&&&&&&&&& LOGIN &&&&&&&&&&&&&&&&&&&&', invoice[0]) #seller[0]["login"]
        
    # pdf, size = html_to_pdf('invoice_template.html', context)
    pdf, size = generate_pdf(seller, invoice)

    if pdf:
        attachment_id = get_attachment_id(request, pdf, size, secret)
        
        if attachment_id:
            pdf_id = put_attachment_id(attachment_id, pdf, secret)

            if pdf_id:
                send_message(attachment_id, secret, invoice[0])


def get_attachment_id(request, pdf, size, secret):
    
    url = f"https://api.allegro.pl.allegrosandbox.pl/messaging/message-attachments"  #messaging/messages"
    headers = {'Authorization': f'Bearer {secret["access_token"]}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-Type': "application/vnd.allegro.public.v1+json"}

    # print('@@@@@@@@@ filename @@@@@@@@@', os.path.basename(pdf))

    data = {
        "filename": os.path.basename(pdf),
        "size": size
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if 'error' in result:
        pass
                    
    # print('@@@@@@@@@ ATTACHMENT_ID @@@@@@@@@', json.dumps(result, indent=4))

    return result


import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

def generate_pdf(seller, invoice):
    pdf_file_path = os.path.join('invoices', 'myfile.pdf')
    # Ensure the directory exists
    os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)

    buyer_info = {
        'name': invoice[2]['company']['name'],
        'taxId': invoice[2]['company']['taxId'],
        'street': invoice[2]['street'],
        'city': invoice[2]['city'],
        'zipCode': invoice[2]['zipCode'],
        'countryCode': invoice[2]['countryCode']
    }

    products = [
        {
            'id': item['id'],
            'offer': {
                'id': item['offer']['id'],
                'name': item['offer']['name'],
                'external': item['offer']['external'],
                'productSet': item['offer']['productSet']
            },
            'quantity': item['quantity'],
            'price': item['price'],
            'tax': item['tax'],
            'reconciliation': item['reconciliation'],
            'selectedAdditionalServices': item['selectedAdditionalServices'],
            'vouchers': item['vouchers'],
            'boughtAt': item['boughtAt']
        }
        for item in invoice[3]
    ]

    c = canvas.Canvas(pdf_file_path, pagesize=A4)
    width, height = A4

    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

    # Set up styles
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    title_style = styles['Title']
    normal_style.wordWrap = 'CJK'  # Enable wrapping
    normal_style.fontSize = 6
    normal_style.fontName = 'DejaVuSans'  # Set the font to the registered font supporting Polish characters
    normal_style.encoding = 'utf-8'  # Set the encoding to UTF-8

    # Add title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(2 * cm, height - 2 * cm, "Faktura")
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, height - 2.5 * cm, "nr: 4/2021")

    # Add seller info
    c.drawString(2 * cm, height - 4 * cm, "Sprzedawca:")
    c.drawString(2 * cm, height - 4.5 * cm, f"{seller['company'].encode('latin-1').decode('utf-8')}")
    c.drawString(2 * cm, height - 5 * cm, f"ul. {seller['street']} {seller['streetNumber']}, {seller['postalCode']} {seller['city']}")
    c.drawString(2 * cm, height - 5.5 * cm, f"NIP {seller['id']}")
    c.drawString(2 * cm, height - 6 * cm, f"Telefon {seller['phone']}")
    c.drawString(2 * cm, height - 6.5 * cm, f"E-mail: {seller['email']}")

    # Add buyer info
    c.drawString(12 * cm, height - 4 * cm, "Nabywca:")
    c.drawString(12 * cm, height - 4.5 * cm, buyer_info['name'])
    c.drawString(12 * cm, height - 5 * cm, f"ul. {buyer_info['street'].encode('latin-1').decode('utf-8')}, {buyer_info['zipCode']} {buyer_info['city']}")
    c.drawString(12 * cm, height - 5.5 * cm, f"NIP {buyer_info['taxId']}")

    # Tekst z polskimi znakami diakrytycznymi
    import unicodedata
    text_with_polish_chars = {'text': "Data zakończenia dostawy/usługi: 07-03-2021"}

    # Normalizacja tekstu
    # normalized_text = unicodedata.normalize('NFKD', text_with_polish_chars).encode('latin-1').decode('utf-8')

    # Add invoice details
    c.drawString(2 * cm, height - 7.5 * cm, "Wystawiona w dniu: 07-03-2021, Warszawa")
    c.drawString(2 * cm, height - 8 * cm, Paragraph(text_with_polish_chars['text'], normal_style))

    # Table data
    data = [
        ["Lp.", "Nazwa towaru lub usługi", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]
    ]

    total_netto = 0
    total_vat = 0
    total_brutto = 0

    for i, product in enumerate(products, start=1):
        name = Paragraph(product['offer']['name'], normal_style) 
        # name = Paragraph(product['offer']['name'])
        quantity = product['quantity']
        price_netto = float(product['price']['amount'])
        value_netto = price_netto * quantity
        vat_rate = float(product['tax']['rate'])
        vat_value = value_netto * (vat_rate / 100)
        value_brutto = value_netto + vat_value

        total_netto += value_netto
        total_vat += vat_value
        total_brutto += value_brutto

        data.append([
            str(i), name, "szt.", str(quantity), f"{price_netto:.2f} PLN", f"{value_netto:.2f} PLN", f"{vat_rate:.2f}%", f"{vat_value:.2f} PLN", f"{value_brutto:.2f} PLN"
        ])

    data.append(["", "", "", "", "Razem:", f"{total_netto:.2f} PLN", "", f"{total_vat:.2f} PLN", f"{total_brutto:.2f} PLN"])

    # Create table #["Lp.", "Nazwa towaru lub usługi", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]
    table = Table(data, colWidths=[1 * cm, 6 * cm, 1 * cm, 1 * cm, 2 * cm, 2 * cm, 1.5 * cm, 2 * cm, 2 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Draw the table
    table.wrapOn(c, width, height)
    table.drawOn(c, 2 * cm, height - 16 * cm)

    # Add total amount
    c.drawString(2 * cm, height - 17 * cm, f"Razem do zapłaty: {total_brutto:.2f} PLN")
    c.drawString(2 * cm, height - 17.5 * cm, "Słownie złotych: (jeden tysiąc dziewięćset dziewięćdziesiąt jeden PLN 37/100)")

    # Signature placeholders
    c.drawString(2 * cm, height - 21 * cm, "_______________________________")
    c.drawString(2 * cm, height - 21.5 * cm, "podpis osoby upoważnionej do odbioru faktury")

    c.drawString(12 * cm, height - 21 * cm, "_______________________________")
    c.drawString(12 * cm, height - 21.5 * cm, "podpis osoby upoważnionej do wystawienia faktury")

    # Save the PDF
    c.save()

    pdf_size = os.path.getsize(pdf_file_path)
    return pdf_file_path, pdf_size




# from reportlab.lib.pagesizes import A4
# from reportlab.lib.units import cm
# from reportlab.pdfgen import canvas
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.platypus import Table, TableStyle
# def generate_pdf(seller, invoice):

#     pdf_file_path = os.path.join(settings.BASE_DIR, 'invoices', 'myfile.pdf')
#     # Ensure the directory exists
#     os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)
#     pdf_size = os.path.getsize(pdf_file_path)

#     buyer_info = {
#         'name': invoice[2]['company']['name'],
#         'taxId': invoice[2]['company']['taxId'],
#         'street': invoice[2]['street'],
#         'city': invoice[2]['city'],
#         'zipCode': invoice[2]['zipCode'],
#         'countryCode': invoice[2]['countryCode']
#     }

#     products = [
#         {
#             'id': item['id'],
#             'offer': {
#                 'id': item['offer']['id'],
#                 'name': item['offer']['name'],
#                 'external': item['offer']['external'],
#                 'productSet': item['offer']['productSet']
#             },
#             'quantity': item['quantity'],
#             'price': item['price'],
#             'tax': item['tax'],
#             'reconciliation': item['reconciliation'],
#             'selectedAdditionalServices': item['selectedAdditionalServices'],
#             'vouchers': item['vouchers'],
#             'boughtAt': item['boughtAt']
#         }
#         for item in invoice[3]
#     ]

#     c = canvas.Canvas(pdf_file_path, pagesize=A4)
#     width, height = A4

#     # Set up styles
#     styles = getSampleStyleSheet()
#     normal_style = styles['Normal']
#     title_style = styles['Title']

#     # Add title
#     c.setFont("Helvetica-Bold", 20)
#     c.drawString(2 * cm, height - 2 * cm, "Faktura")
#     c.setFont("Helvetica", 12)
#     c.drawString(2 * cm, height - 2.5 * cm, "nr: 4/2021")

#     # Add seller info
#     c.drawString(2 * cm, height - 4 * cm, "Sprzedawca:")
#     c.drawString(2 * cm, height - 4.5 * cm, f"{seller['company']}")
#     c.drawString(2 * cm, height - 5 * cm, f"ul. {seller['street']} {seller['streetNumber']}, {seller['postalCode']} {seller['city']}")
#     c.drawString(2 * cm, height - 5.5 * cm, f"NIP {seller['id']}")
#     c.drawString(2 * cm, height - 6 * cm, f"Telefon {seller['phone']}")
#     c.drawString(2 * cm, height - 6.5 * cm, f"E-mail: {seller['email']}")

#     # Add buyer info
#     c.drawString(12 * cm, height - 4 * cm, "Nabywca:")
#     c.drawString(12 * cm, height - 4.5 * cm, buyer_info['name'])
#     c.drawString(12 * cm, height - 5 * cm, f"ul. {buyer_info['street']}, {buyer_info['zipCode']} {buyer_info['city']}")
#     c.drawString(12 * cm, height - 5.5 * cm, f"NIP {buyer_info['taxId']}")

#     # Add invoice details
#     c.drawString(2 * cm, height - 7.5 * cm, "Wystawiona w dniu: 07-03-2021, Warszawa")
#     c.drawString(2 * cm, height - 8 * cm, "Data zakończenia dostawy/usługi: 07-03-2021")

#     # Table data
#     data = [
#         ["Lp.", "Nazwa towaru lub usługi", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]
#     ]

#     total_netto = 0
#     total_vat = 0
#     total_brutto = 0

#     for i, product in enumerate(products, start=1):
#         name = product['offer']['name']
#         quantity = product['quantity']
#         price_netto = float(product['price']['amount'])
#         value_netto = price_netto * quantity
#         vat_rate = float(product['tax']['rate'])
#         vat_value = value_netto * (vat_rate / 100)
#         value_brutto = value_netto + vat_value

#         total_netto += value_netto
#         total_vat += vat_value
#         total_brutto += value_brutto

#         data.append([
#             str(i), name, "szt.", str(quantity), f"{price_netto:.2f} PLN", f"{value_netto:.2f} PLN", f"{vat_rate:.2f}%", f"{vat_value:.2f} PLN", f"{value_brutto:.2f} PLN"
#         ])

#     data.append(["", "", "", "", "Razem:", f"{total_netto:.2f} PLN", "", f"{total_vat:.2f} PLN", f"{total_brutto:.2f} PLN"])

#     # Create table
#     table = Table(data, colWidths=[1 * cm, 6 * cm, 1.5 * cm, 1.5 * cm, 2.5 * cm, 3 * cm, 1.5 * cm, 3 * cm, 3 * cm])
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#     ]))

#     # Draw the table
#     table.wrapOn(c, width, height)
#     table.drawOn(c, 2 * cm, height - 16 * cm)

#     # Add total amount
#     c.drawString(2 * cm, height - 17 * cm, f"Razem do zapłaty: {total_brutto:.2f} PLN")
#     c.drawString(2 * cm, height - 17.5 * cm, "Słownie złotych: (jeden tysiąc dziewięćset dziewięćdziesiąt jeden PLN 37/100)")

#     # Signature placeholders
#     c.drawString(2 * cm, height - 21 * cm, "_______________________________")
#     c.drawString(2 * cm, height - 21.5 * cm, "podpis osoby upoważnionej do odbioru faktury")

#     c.drawString(12 * cm, height - 21 * cm, "_______________________________")
#     c.drawString(12 * cm, height - 21.5 * cm, "podpis osoby upoważnionej do wystawienia faktury")

#     # Save the PDF
#     c.save()

#     return pdf_file_path, pdf_size
    

    # if not c.err:
    #     with open(pdf_file_path, "wb") as pdf_file:
    #         pdf_file.write(c)
    #     pdf_size = c
    #     # return HttpResponse(result.getvalue(), content_type='application/pdf')
    #     return pdf_file_path, pdf_size

# ******************************************************

# from django.http import HttpResponse
# from django.views.generic import View
# from django.template.loader import get_template
# from xhtml2pdf import pisa
# def html_to_pdf(template_src, context_dict={}):
#     template = get_template(template_src)
#     html = template.render(context_dict)
#     result = io.BytesIO()
#     pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-2")), result)

#     pdf_file_path = os.path.join(settings.BASE_DIR, 'invoices', 'myfile.pdf')
#     # Ensure the directory exists
#     os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)

#     if not pdf.err:
#         with open(pdf_file_path, "wb") as pdf_file:
#             pdf_file.write(result.getvalue())
#         pdf_size = result.tell()
#         # return HttpResponse(result.getvalue(), content_type='application/pdf')
#         return pdf_file_path, pdf_size
    

def put_attachment_id(attachment_id, pdf, secret):
    
    url = f"https://api.allegro.pl.allegrosandbox.pl/messaging/message-attachments/{attachment_id['id']}"
    headers = {
        'Authorization': f'Bearer {secret["access_token"]}', 
        'Accept': "application/vnd.allegro.public.v1+json", 
        'Content-Type': "application/pdf"
        }
        
    with open(pdf, 'rb') as f:
        file_content = f.read()
        
    files = {
        'file': (os.path.basename(pdf), file_content, 'application/pdf')
    }

    response = requests.put(url, headers=headers, files=files)
    result = response.json()

    # print('@@@@@@@@@ ATTCH @@@@@@@@@', json.dumps(result, indent=4))
    # print('@@@@@@@@@ ATTCH HEADERS @@@@@@@@@', response.headers)

    if 'error' in result:
        pass

    return result


def send_message(attachment_id, secret, recipient):
    
    url = f"https://api.allegro.pl.allegrosandbox.pl/messaging/messages"
    headers = {'Authorization': f'Bearer {secret["access_token"]}', 'Accept': "application/vnd.allegro.public.v1+json", 'Content-Type': "application/vnd.allegro.public.v1+json"}

    data = {
        "recipient": {
            "login": recipient
        },
        "text": "tests-8",
        "attachments": [
            {"id": attachment_id['id']}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if 'error' in result:
        pass
                                
    # print('@@@@@@@@@ INVOICE @@@@@@@@@', json.dumps(result, indent=4))
    # print('@@@@@@@@@ INVOICE HEADERS @@@@@@@@@', response.headers)








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