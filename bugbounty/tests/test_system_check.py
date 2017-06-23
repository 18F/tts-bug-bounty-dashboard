import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_system_check_works():
    call_command('check', '--fail-level', 'WARNING')
