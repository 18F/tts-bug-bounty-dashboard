from itertools import chain
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


class ProgramConfiguration:
    '''
    Represents a HackerOne program's configuration, e.g. the credentials
    required to glean information about it via the HackerOne API.
    '''

    MAX_PROGRAMS = 100

    def __init__(self, handle, api_username, api_password):
        self.handle = handle
        self.api_username = api_username
        self.api_password = api_password

    def find_reports(self, **kwargs):
        '''
        Find all HackerOne reports for the program, passing any
        keyword arguments on to HackerOneClient.find_resources().
        '''

        client = HackerOneClient(self.api_username, self.api_password)
        return client.find_resources(h1_models.Report,
                                     program=[self.handle],
                                     **kwargs)

    @classmethod
    def parse(cls, env_var):
        '''
        Parse a ProgramConfiguration from an environment variable
        string formatted as the program handle, API username and
        password separated by colons, e.g. "tts:apiuser:apipass".
        '''

        return cls(*env_var.split(':', maxsplit=2))

    @classmethod
    def parse_list_from_environ(cls, prefix, environ):
        '''
        Parse a list of ProgramConfiguration objects from the
        given environment dictionary, assuming that each object
        has a common prefix followed by an integer (starting at 1).
        '''

        programs = []

        for i in range(1, cls.MAX_PROGRAMS):
            name = f'{prefix}{i}'
            if name in environ:
                programs.append(cls.parse(environ[name]))
            else:
                break
        return programs


def find_reports(**kwargs):
    '''
    Find HackerOne reports for *all* programs, passing any keyword
    arguments to ProgramConfiguration.find_reports().
    '''

    from django.conf import settings

    return chain(*[program.find_reports(**kwargs)
                   for program in settings.H1_PROGRAMS])
