from re import L
from django.http import HttpResponse
import logging


logger = logging.getLogger("logger_name")

def index(request):
    logger.warning("Test6")
    return HttpResponse("Hello, world. You're at the polls index.")