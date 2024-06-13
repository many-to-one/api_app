import os
import time
from ..views import get_next_token
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

from ..models import *
from .serializers import *
from django.http import HttpResponse
from django.shortcuts import render
import requests
import json

import io
import PyPDF2
from datetime import datetime



def get_order_details(request, id, name, secret):

    try:
        url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{id}"
        headers = {'Authorization': f'Bearer {secret.access_token}', 'Accept': "application/vnd.allegro.public.v1+json"}
        product_result = requests.get(url, headers=headers, verify=True)
        result = product_result.json()
        if 'error' in result:
            error_code = result['error']
            if error_code == 'invalid_token':
                # print('ERROR RESULT @@@@@@@@@', error_code)
                try:
                    # Refresh the token
                    new_token = get_next_token(request, secret.refresh_token, name)
                    # Retry fetching orders with the new token
                    return get_order_details(request, id)
                except Exception as e:
                    print('Exception @@@@@@@@@', e)
                    context = {'name': name}
                    return render(request, 'invalid_token.html', context)

        # print('@@@@@@@@@ GET ORDER DETAILS @@@@@@@@@', json.dumps(result, indent=4))
        context = {
            'order': product_result.json()
        }
        return [result]
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)



def get_invoice_file(request, name, buyer):

    start_time = time.time()

    address = Address.objects.get(name__name=name)
    address_data = AddressSerializer(address).data
    secret = Secret.objects.get(account__name=name) 
    # print('********************** SECRET ****************************', secret)

    ids = request.GET.getlist('ids')
    # print('********************** IDS set_shipment_list IDS ****************************', ids)

    separated_ids = []
    for id_string in ids:
        separated_ids.extend(id_string.split(','))

    results = []
    for id in separated_ids:
        res = get_order_details(request, id, name, secret)
        results.append(res)
        # print('********************** ORDER DETAILS ****************************', res)

    # print('********************** ORDER DETAILS ****************************', results)
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

            tasks_.append(invoice_template(request, address_data, tasks, secret))
    if tasks_:
        response = base64_to_pdf_bulk(tasks_)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"********************** FINISH time: {elapsed_time} seconds **********************")
    return response


def base64_to_pdf_bulk(base64_data_list):

    pdf_writer = PyPDF2.PdfWriter()

    try:
        for base64_data in base64_data_list:
            # print(' @@@@@@@@@@@@@@@@@ INSIDE base64_data @@@@@@@@@@@@@@@@@ ', base64_data)
            # Decode the Base64 data
            if base64_data is not None:
                binary_data = base64_data #base64.b64decode(base64_data)
                # print(' @@@@@@@@@@@@@@@@@ INSIDE binary_data @@@@@@@@@@@@@@@@@ ', binary_data)

                # Create a PdfReader object
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(binary_data))
                # print(' @@@@@@@@@@@@@@@@@ INSIDE pdf_reader @@@@@@@@@@@@@@@@@ ', pdf_reader)

                # Merge each page from the PdfReader object into the PdfWriter object
                for page_num in range(len(pdf_reader.pages)):
                    pdf_writer.add_page(pdf_reader.pages[page_num])
            else:
                None

        # Create a BytesIO buffer to write the merged PDF
        output_buffer = io.BytesIO()
        # print(' @@@@@@@@@@@@@@@@@ INSIDE output_buffer @@@@@@@@@@@@@@@@@ ') #output_buffer
        pdf_writer.write(output_buffer)

        # Set the appropriate content type for PDF
        response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')

        # Optionally, set a filename for the downloaded PDF
        response['Content-Disposition'] = 'attachment; filename="fv.pdf"'
        return response
    except Exception as e:
        print("Error:", e)


def invoice_template(request, seller, invoice, secret):
    # print('******************* invoice_template ******************',seller, invoice)

    #iterate invoice!!!
    # for invoice in invoices:
    # print('&&&&&&&&&&&&&&&&&&& seller &&&&&&&&&&&&&&&&&&&&', seller)
    # print('&&&&&&&&&&&&&&&&&&& invoice &&&&&&&&&&&&&&&&&&&&', invoice)
    context = {
            'seller': seller,  
            'payment': invoice[0],
            'customer': invoice[1],  
            'order': invoice[2],  
        }
        
    # print('&&&&&&&&&&&&&&&&&&& LOGIN &&&&&&&&&&&&&&&&&&&&', invoice[0]) #seller[0]["login"]

    pdf = generate_pdf(seller, invoice)
    return pdf


def generate_pdf(seller, invoice):

    now = datetime.now()

    # day = now.day
    # month = now.month
    year = now.year
    formatted_date = now.strftime("%d-%m-%Y")

    buffer = io.BytesIO()

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

    c = canvas.Canvas(buffer, pagesize=A4)
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
    c.setFont("DejaVuSans", 10)
    c.drawString(2 * cm, height - 2 * cm, "Faktura")
    c.drawString(2 * cm, height - 2.5 * cm, f"nr: 4/{year}")

    # Add seller info
    c.drawString(2 * cm, height - 4 * cm, "Sprzedawca:")
    c.drawString(2 * cm, height - 4.5 * cm, f"{seller['company']}")
    c.drawString(2 * cm, height - 5 * cm, f"ul. {seller['street']} {seller['streetNumber']}, {seller['postalCode']} {seller['city']}")
    c.drawString(2 * cm, height - 5.5 * cm, f"NIP {seller['id']}")
    c.drawString(2 * cm, height - 6 * cm, f"Telefon {seller['phone']}")
    c.drawString(2 * cm, height - 6.5 * cm, f"E-mail: {seller['email']}")

    # Add buyer info
    c.drawString(12 * cm, height - 4 * cm, "Nabywca:")
    c.drawString(12 * cm, height - 4.5 * cm, buyer_info['name'])
    c.drawString(12 * cm, height - 5 * cm, f"ul. {buyer_info['street']}, {buyer_info['zipCode']} {buyer_info['city']}")
    c.drawString(12 * cm, height - 5.5 * cm, f"NIP {buyer_info['taxId']}")

    # Tekst z polskimi znakami diakrytycznymi
    import unicodedata
    text_with_polish_chars = {'text': f"Data zakończenia dostawy/usługi: {formatted_date}"}

    # Normalizacja tekstu
    # normalized_text = unicodedata.normalize('NFKD', text_with_polish_chars).encode('latin-1').decode('utf-8')

    # Add invoice details
    c.drawString(2 * cm, height - 7.5 * cm, f"Wystawiona w dniu: {formatted_date}, {seller['city']}")
    c.drawString(2 * cm, height - 8 * cm, text_with_polish_chars['text'])

    # Table data
    data = [
        ["Lp.", "Nazwa towaru lub usługi", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]
    ]

    total_netto = 0
    total_vat = 0
    total_brutto = 0

    for i, product in enumerate(products, start=1):
        name = Paragraph(product['offer']['name'], normal_style) 
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
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Draw the table
    table.wrapOn(c, width, height)
    table.drawOn(c, 2 * cm, height - 16 * cm)

    # Add total amount
    c.drawString(2 * cm, height - 17 * cm, f"Razem do zapłaty: {total_brutto:.2f} PLN")
    # c.drawString(2 * cm, height - 17.5 * cm, f"Słownie złotych: ({num2words(total_brutto, lang='pl')} PLN 37/100)")

    # Signature placeholders
    c.drawString(2 * cm, height - 21 * cm, "_______________________________")
    c.drawString(2 * cm, height - 21.5 * cm, "podpis osoby upoważnionej do odbioru faktury")

    c.drawString(12 * cm, height - 21 * cm, "_______________________________")
    c.drawString(12 * cm, height - 21.5 * cm, "podpis osoby upoważnionej")
    c.drawString(12 * cm, height - 22 * cm, "do wystawienia faktury")

    # Save the PDF
    c.save()

    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content
