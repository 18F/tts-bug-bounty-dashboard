import os
import json

Environ = os._Environ


def is_on_cloudfoundry(env: Environ=os.environ) -> bool:
    return 'VCAP_SERVICES' in env


def load_cups_from_vcap_services(name: str, env: Environ=os.environ) -> None:
    '''
    Detects if VCAP_SERVICES exists in the environment; if so, parses
    it and imports all the credentials from the given custom
    user-provided service (CUPS) as strings into the environment.
    For more details on CUPS, see:
    https://docs.cloudfoundry.org/devguide/services/user-provided.html
    '''

    if not is_on_cloudfoundry(env):
        return

    vcap = json.loads(env['VCAP_SERVICES'])

    for entry in vcap.get('user-provided', []):
        if entry['name'] == name:
            for key, value in entry['credentials'].items():
                env[key] = value
