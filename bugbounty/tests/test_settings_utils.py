import unittest
import json

from ..settings_utils import load_cups_from_vcap_services, load_database_url_from_vcap_services


def make_vcap_services_env(vcap_services):
    return {
        'VCAP_SERVICES': json.dumps(vcap_services)
    }


class CupsTests(unittest.TestCase):

    def test_noop_if_vcap_services_not_in_env(self):
        env = {}
        load_cups_from_vcap_services('blah', env=env)
        self.assertEqual(env, {})

    def test_irrelevant_cups_are_ignored(self):
        env = make_vcap_services_env({
            "user-provided": [
                {
                    "label": "user-provided",
                    "name": "NOT-boop-env",
                    "syslog_drain_url": "",
                    "credentials": {
                        "boop": "jones"
                    },
                    "tags": []
                }
            ]
        })

        load_cups_from_vcap_services('boop-env', env=env)

        self.assertFalse('boop' in env)

    def test_credentials_are_loaded(self):
        env = make_vcap_services_env({
            "user-provided": [
                {
                    "label": "user-provided",
                    "name": "boop-env",
                    "syslog_drain_url": "",
                    "credentials": {
                        "boop": "jones"
                    },
                    "tags": []
                }
            ]
        })

        load_cups_from_vcap_services('boop-env', env=env)

        self.assertEqual(env['boop'], 'jones')

def test_database_settings_loaded():
    db_uri = "this is the database url"
    env = make_vcap_services_env({"aws-rds": [{"credentials": {"uri": db_uri}}]})
    load_database_url_from_vcap_services("boop-env", "aws-rds", env=env)
    assert env['DATABASE_URL'] == db_uri