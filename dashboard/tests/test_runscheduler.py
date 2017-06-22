from unittest import mock
import pytest
from django.core.management import call_command

from dashboard.management.commands import runscheduler, h1sync


def call_runscheduler(loops=1, mock_call_command=None):
    ctx = {'sleep_count': 0}

    def fake_sleep(seconds):
        ctx['sleep_count'] += 1
        if ctx['sleep_count'] > loops:
            raise KeyboardInterrupt()

    if mock_call_command is None:
        mock_call_command = mock.MagicMock()

    with mock.patch.object(runscheduler, 'call_command', mock_call_command):
        with mock.patch.object(runscheduler, 'logger') as mock_logger:
            with mock.patch('time.sleep', fake_sleep):
                with pytest.raises(KeyboardInterrupt):
                    call_command('runscheduler')
            return mock_call_command, mock_logger


def test_it_calls_h1sync():
    mock_call_command, mock_logger = call_runscheduler()
    cmd = mock_call_command.call_args_list[0][0][0]
    assert isinstance(cmd, h1sync.Command)
    mock_logger.info.assert_any_call(
        'Running "manage.py h1sync".'
    )
    mock_logger.exception.assert_not_called()


def test_it_catches_and_logs_exceptions():
    mock_call_command = mock.MagicMock()
    mock_call_command.side_effect = Exception('KABOOM')
    _, mock_logger = call_runscheduler(mock_call_command=mock_call_command)
    mock_logger.exception.assert_any_call(
        'An error occurred when running "manage.py h1sync".'
    )
