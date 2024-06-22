import csv
import io
import json, requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from ..utils import *
from ..models import *

def bulk_edit(request, name, ed_value):

    ids = request.GET.getlist('ids')
    encoded_offers = ','.join(ids)
    print('********************** ids ****************************', ids)

    return redirect(f'{ed_value}', name=name, offers=encoded_offers)


def PRICE(request, name, offers):


    offers_list = [{'id': offer_id} for offer_id in offers.split(',')]

    if request.method == 'POST':
        price = request.POST.get('price')


        print('********************** price ****************************', price)

    return render(request, 'bulk_price.html')