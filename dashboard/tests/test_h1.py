from django.test import override_settings
from unittest import mock

from .. import h1


@override_settings(H1_API_USERNAME='foo', H1_API_PASSWORD='bar',
                   H1_PROGRAM='baz')
@mock.patch('dashboard.h1.HackerOneClient')
def test_find_reports_works(fake_client_class):
    fake_client = mock.MagicMock()
    fake_client_class.return_value = fake_client
    fake_client.find_resources.return_value = "stuff"

    result = h1.find_reports(blah=1)

    assert result == "stuff"
    fake_client_class.assert_called_once_with('foo', 'bar')
    fake_client.find_resources.assert_called_once_with(
        h1.h1_models.Report,
        program=['baz'],
        blah=1
    )


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
