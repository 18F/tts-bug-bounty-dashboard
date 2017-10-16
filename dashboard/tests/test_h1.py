from django.test import override_settings
from unittest import mock

from .. import h1
from h1 import models as h1_models


@override_settings(H1_PROGRAMS=[
    h1.ProgramConfiguration(handle='baz',
                            api_username='foo',
                            api_password='bar')
])
@mock.patch('dashboard.h1.HackerOneClient')
def test_find_reports_works(fake_client_class):
    fake_client = mock.MagicMock()
    fake_client_class.return_value = fake_client
    fake_client.find_resources.return_value = ["stuff"]

    results = [r for r in h1.find_reports(blah=1)]

    assert results == ["stuff"]
    fake_client_class.assert_called_once_with('foo', 'bar')
    fake_client.find_resources.assert_called_once_with(
        h1.h1_models.Report,
        program=['baz'],
        blah=1
    )


def test_program_configuration_parse_works():
    pc = h1.ProgramConfiguration.parse('prog:user:pass:!?:')
    assert pc.handle == 'prog'
    assert pc.api_username == 'user'
    assert pc.api_password == 'pass:!?:'


def test_program_configuration_parse_list_from_environ_works():
    pcs = h1.ProgramConfiguration.parse_list_from_environ(
        environ={
            'H1_PROGRAM_1': 'a:b:c',
            'H1_PROGRAM_2': 'd:e:f',
        },
        prefix='H1_PROGRAM_',
    )
    assert len(pcs) == 2

    assert pcs[0].handle == 'a'
    assert pcs[0].api_username == 'b'
    assert pcs[0].api_password == 'c'

    assert pcs[1].handle == 'd'
    assert pcs[1].api_username == 'e'
    assert pcs[1].api_password == 'f'


def test_newer_report_works():
    report = h1.NewerReport(None, {
        'type': 'report',
        'attributes': {
            'created_at': '2016-02-02T04:05:06.000Z',
            'last_activity_at': None,
            'first_program_activity_at': None,
            'last_program_activity_at': None,
            'last_reporter_activity_at': None,
            'triaged_at': None,
            'swag_awarded_at': None,
            'bounty_awarded_at': None,
            'closed_at': None,
            'disclosed_at': None,
            'title': 'XSS in login form',
            'state': 'new',
        },
        'relationships': {
            'structured_scope': {
                'data': {
                    "id": "57",
                    "type": "structured-scope",
                    "attributes": {
                        "asset_identifier": "api.example.com",
                        "asset_type": "url",
                        "confidentiality_requirement": "high",
                        "integrity_requirement": "high",
                        "availability_requirement": "high",
                        "max_severity": "critical",
                        "created_at": "2015-02-02T04:05:06.000Z",
                        "updated_at": "2016-05-02T04:05:06.000Z",
                        "instruction": None,
                        "eligible_for_bounty": True,
                        "eligible_for_submission": True
                    }
                }
            }
        }
    })

    assert report.structured_scope.asset_identifier == 'api.example.com'
    assert report.structured_scope.asset_type == 'url'
    assert report.structured_scope.eligible_for_bounty is True

def test_bounty_amounts_containing_commas():
    # Frustratingly, h1's API returns bounty amounts over 999 that contain
    # commas. This tests that our monkeypatch handles this correctly.
    b = h1_models.Bounty(None, {
        'type': 'bounty',
        'attributes': {
            'created_at': '2016-02-02T04:05:06.000Z',
            'amount': '2,000',
            'bonus_amount': '1,500'
        }
    })
    assert b.amount == 2000
