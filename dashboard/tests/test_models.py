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


def new_triaged_report(triage_days=1, **kwargs):
    year = 2017
    month = 6
    day = 19  # A monday
    hour = 14  # In the middle of the day UTC, during business hours EST
    return new_report(
        created_at=datetime(year, month, day, hour, tzinfo=pytz.utc),
        triaged_at=datetime(year, month, day + triage_days, hour,
                            tzinfo=pytz.utc),
        **kwargs
    )


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
    r = new_triaged_report(triage_days=1)
    r.save()
    assert r.days_until_triage == 1


def test_percentage_works_when_denominator_is_nonzero():
    assert percentage(18, 100) == 18


def test_percentage_works_when_denominator_is_zero():
    assert percentage(18, 0, default=15) == 15


@pytest.mark.django_db
def test_get_stats_reports_triage_accuracy():
    new_report(id=1, is_accurate=True).save()
    new_report(id=2, is_accurate=False).save()
    assert Report.get_stats()['triage_accuracy'] == 50


@pytest.mark.django_db
def test_get_stats_reports_false_negatives():
    new_report(id=1, is_false_negative=True).save()
    new_report(id=2, is_false_negative=False).save()
    assert Report.get_stats()['false_negatives'] == 50


@pytest.mark.django_db
def test_get_stats_reports_triaged_within_one_day():
    new_report(id=1).save()
    new_triaged_report(triage_days=1, id=2).save()
    new_triaged_report(triage_days=2, id=3).save()
    assert Report.get_stats()['triaged_within_one_day'] == 50


@pytest.mark.django_db
def test_get_stats_returns_defaults_when_counts_are_zero():
    assert Report.get_stats() == {
        'triage_accuracy': 100,
        'false_negatives': 0,
        'triaged_within_one_day': 100,
    }
