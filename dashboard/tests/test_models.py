import pytest
import pytz
from datetime import datetime
from django.utils.timezone import now

from ..models import Report, percentage


def new_report(**kwargs):
    right_now = now()
    return Report(**{**dict(
        id=12345,
        title='a report',
        created_at=right_now,
        state='new',
        last_synced_at=right_now
    ), **kwargs})


def test_get_absolute_url_works():
    r = new_report(id=4567)
    assert r.get_absolute_url() == 'https://hackerone.com/reports/4567'


@pytest.mark.django_db
def test_save_sets_days_until_triage_to_none_if_untriaged():
    r = new_report(triaged_at=None)
    r.save()
    assert r.days_until_triage is None


@pytest.mark.django_db
def test_save_sets_days_until_triage_to_value_if_triaged():
    r = new_report(
        created_at=datetime(2017, 6, 21, 14, tzinfo=pytz.utc),
        triaged_at=datetime(2017, 6, 22, 14, tzinfo=pytz.utc),
    )
    r.save()
    assert r.days_until_triage == 1


def test_percentage_works_when_denominator_is_nonzero():
    assert percentage(18, 100) == 18


def test_percentage_works_when_denominator_is_zero():
    assert percentage(18, 0, default=15) == 15
