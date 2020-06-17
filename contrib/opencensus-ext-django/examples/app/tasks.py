from celery import shared_task
import random

@shared_task
def create(total):
    return random.choices([1,2,3])
