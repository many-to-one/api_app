import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from ..utils import *
import requests
from ..models import *
import base64


def ebay_token(request):

    token='v^1.1#i^1#p^1#f^0#I^3#r^0#t^H4sIAAAAAAAAAOVYa2wURRy/6wOogDWgWEgDl8VEse7rXu2u3JnrtaSn9AF3bZEIZG53th1ub/fcnW3vRJJalGijmIgfJI2kAUNIBC0JBqESqiAhSFSQL8TEiBHDBwwVYzDxg85ej3KtpBR6iU28D7eZmf/zN//HzHA9s8qe3N6w/eZ85+yigR6up8jp5OdyZbNKqx4sLlpS6uDyCJwDPY/1lPQWX11pgqSaEtdCM6VrJnSlk6pmitnJAGUZmqgDE5miBpLQFLEkRkONq0U3w4kpQ8e6pKuUK1IXoKoVHgBB8QuAq+Hc1QKZ1W7JjOkBSq6RvB6/188LhNAtSGTdNC0Y0UwMNByg3JzbS3Ne2u2PcdWiRxB9Xqaa862nXG3QMJGuERKGo4JZc8Usr5Fn6+SmAtOEBiZCqGAktCraHIrU1TfFVrJ5soI5HKIYYMscPwrrMnS1AdWCk6sxs9Ri1JIkaJoUGxzVMF6oGLplzH2Yn4VakhTF75EUXpIljwwKA+Uq3UgCPLkd9gySaSVLKkINI5y5G6IEjfhmKOHcqImIiNS57M8aC6hIQdAIUPW1oedDLS1UsFmFCROhGB2DJqajtetoyEHI+yRZoAWocP4aL8gpGZWUg3iClrCuycgGzHQ16bgWEovhRFzcebgQomat2Qgp2LYmn07I4ecXatbbGzq6gxbu1Ow9hUkCgis7vDv6Y9wYGyhuYTgmYeJCFp4ABVIpJFMTF7NxmAudtBmgOjFOiSzb3d3NdHsY3ehg3RzHs+saV0elTpgEVI7WzvW0ie7OQKOsKxIknCYScSZFbEmTOCUGaB1U0OvmeLc3h/t4s4ITZ/81keczOz4bCpUdoNrjkf2kzvj9EicAdyGyI5gLUNa2A8ZBhk4CIwFxSgUSpCUSZ1YSGkgWPT7F7alRIC37BYX2CopCx32yn+YVaAdyPC4JNf+XJJlqmEehZEBcsDgvSIxnuhCSIkaYTybcaS2RQquSbY2+hpCVbvW3K/F14aq16Zgaro+zemCqmXBH58MqIsjEiP5CAmDn+vRBaNBNDOVpuReV9BRs0VUkZWbWBnsMuQUYOFNrZcg4ClWVfKblaiiVihSuWhfEyXsoFPfnc2E71H/Qne7olWkH7czyyuY3iQCQQozdfxhJT7I6IAcP1s51Mr0pa7VrEsIxIjZuZZgOi8QEsUQmZ78pMyFSyBnSyuSps4w2SuLE1FnIxUK2JHxfirIdmSFooo5ObN6TzvR0QIlbamLqLDIE6rRCFJHrxYwKUOLpqMtIHr0XMFm/GbNLYgxo6pZBrkRMs31UjukJqJHDBzZ0VYVGGz/tsptMWhjEVTjT6m8BahEC+Sejkl7n1RngF1/Ne3nyJ0zPNyl79tk00zpIIbvmPdx+2PHvMEFH9sf3Os9yvc7TRU4nV8fRfBW3YlZxa0nxPMokdYcxgSbH9TSDgMKQkqcBbBmQScBMCiCjaKHjqxcdT/U80MAO9r3QWxXbnHHMyXsOGtjAVYw9CJUV83PzXoe4ytsrpXz5o/PdXs7r9nPVHsHnXc8tv71awi8qeVg+PvLe5ktN84b/eGKLsKKVnV2OrnDzx4iczlIHiV1HU+k3TElfGLl2Xu7qevWRD9u+HU6M7D67Txt8aFFf/7WbnUGpdl750NdHP+67VNl3qurA660bRyrePLiwfNfF7dc+em3/sd+1z2+0LRg5dDKuLTza6BzcRd2wUH9UmjNwqPTPpZlfLvxdu2PI2Cru2bjoyODbw/tSxysb9u49hz84trVmyXBH3zOSMQSWRpA+9PLF2gvPVpx/aUslFfvh6Ve+XLwBvvWj6yAd+WxZ+07m3e8eb2fPbNlxov/ctjNLNu257ji5e0391fCvP33f3/Lb8f3M4Yp3in6ee+Fw/Rs3F7Rv2PbX8stvMP6i+Mn3T+w4sPqTsk8rgl8sPXXkHBU677h0xXc6ITy3bPH10T39By4UJ0OoEwAA'

    client_id = 'OleksiiT-Test-SBX-e0ee15cd9-9ef0684a'
    secret_id = 'SBX-0ee15cd95b8e-9cb8-4401-ba2f-52ce'
    base64_data = f"{client_id}:{secret_id}"
    binary_data = base64.b64encode(base64_data.encode())
    # binary_data = base64.b64encode(b'OleksiiT-Test-SBX-e0ee15cd9-9ef0684a:SBX-0ee15cd95b8e-9cb8-4401-ba2f-52ce')
    url = 'https://api.sandbox.ebay.com/identity/v1/oauth2/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {binary_data}',
    }
    data = {
        'grant_type': 'client_credentials',
        'scope': 'https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.item.bulk'
    }

    response = requests.post(url, headers=headers, data=data)
    print('**************** EBAY RESPONSE ******************', response.json())
    if response.status_code == 200:
        print('**************** EBAY RESPONSE 200 ******************', response.json())
        access_token = response.json().get('access_token')
        print('**************** EBAY TOKEN ******************', access_token)
        return HttpResponse(f'{access_token}')
    else:
        print('Error:', response.text)
        return HttpResponse(f'{response.text}')

