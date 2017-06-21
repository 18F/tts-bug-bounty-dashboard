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
