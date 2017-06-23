from django.conf import settings
from h1.client import HackerOneClient
from h1 import models as h1_models


class NewerReport(h1_models.Report):
    '''
    The schema for the h1 package's Report class is out-of-date and
    doesn't include some fields that we need.

    So, this overrides the Report class defined at:

        https://github.com/uber-common/h1-python/blob/master/h1/models.py

    Note that due to the way the h1 package uses metaclasses, just
    *declaring* this subclass, and having it inherit its `TYPE` attribute
    from its superclass, automatically registers it as a type hydrator
    that overrides its superclass.

    In other words, even though this class isn't explicitly *used* by
    any of our code, it will automatically be used by the h1 package
    when the HackerOne API is queried.
    '''

    def _hydrate(self):
        super()._hydrate()
        self._make_relationship("structured_scope", self._hydrate_object)


class StructuredScope(h1_models.HackerOneObject):
    '''
    This represents the HackerOne API's StructuredScope, documented at:

        https://api.hackerone.com/docs/v1#structured-scope

    The h1 package doesn't include this type, so we need to add it.
    '''

    # This attribute automatically registers this class as a type hydrator.
    TYPE = 'structured-scope'

    def _hydrate(self):
        self._make_attribute("asset_identifier", self._hydrate_verbatim)
        self._make_attribute("asset_type", self._hydrate_verbatim)
        self._make_attribute("eligible_for_bounty", self._hydrate_verbatim)


def find_reports(**kwargs):
    client = HackerOneClient(settings.H1_API_USERNAME,
                             settings.H1_API_PASSWORD)
    return client.find_resources(h1_models.Report,
                                 program=[settings.H1_PROGRAM],
                                 **kwargs)
