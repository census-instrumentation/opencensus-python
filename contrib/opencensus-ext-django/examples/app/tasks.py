import random

from celery import shared_task


@shared_task
def create(total):
    return random.choices([1,2,3])
