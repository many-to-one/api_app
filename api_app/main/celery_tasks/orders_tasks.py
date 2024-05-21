# tasks.py

import time
from celery import shared_task
# from ..views_folder.orders_views_test import get_pickup_proposals, get_courier
from ..views_folder import orders_views_test

@shared_task
def my_new_task(shipmentId, secret, commandId):
    print('######### CELERY shipmentId ###########', shipmentId)
    print('######### CELERY secret ###########', secret)
    print('######### CELERY commandId ###########', commandId)
    # pickupDateProposalId = await orders_views_test.get_pickup_proposals(secret, shipmentId)
    # if pickupDateProposalId:
    #     await orders_views_test.get_courier(shipmentId, commandId, pickupDateProposalId, secret)


@shared_task
async def my_task():
    print('######### CELERY shipmentId ###########')
