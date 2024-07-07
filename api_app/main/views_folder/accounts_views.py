from django.http import JsonResponse
from django.shortcuts import render, redirect
from ..models import *
from ..utils import *

def add_account(request):

    if request.user.is_authenticated:

        user = get_user(request)

        if request.method == 'POST':
            NAME = request.POST.get('NAME')
            CLIENT_ID = request.POST.get('CLIENT_ID')
            CLIENT_SECRET = request.POST.get('CLIENT_SECRET')

            try:
                account = Allegro.objects.create(
                    name=NAME,
                    user=user,
                )
                account.save()

                account_secret = Secret.objects.create(
                    CLIENT_ID=CLIENT_ID,
                    CLIENT_SECRET=CLIENT_SECRET,
                    account=account,
                )
                account_secret.save()
                if account_secret:
                    return JsonResponse({
                        'message': 'success',
                        'text': f'Konto {NAME} zostało powiązane!',
                    })
                else:
                    pass

            except Exception as e:
                pass

        return render(request, 'add_account.html')
