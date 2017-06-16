from django.conf import settings
from h1.client import HackerOneClient
from h1 import models as h1_models


def find_reports(**kwargs):
    client = HackerOneClient(settings.H1_API_USERNAME,
                             settings.H1_API_PASSWORD)
    return client.find_resources(h1_models.Report,
                                 program=[settings.H1_PROGRAM],
                                 **kwargs)
