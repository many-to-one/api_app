from django.shortcuts import render
import requests
from main.models import *


def get_accounts(request):
    accounts = Allegro.objects.filter(user=request.user.id).all()
    return {
        'accounts': accounts,
    }

    # return render(request, 'get_accounts.html', context)

