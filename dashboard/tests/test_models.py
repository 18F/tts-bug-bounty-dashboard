import pytest
import pytz
from datetime import datetime
from django.utils.timezone import now

from ..models import (
    Report, SingletonMetadata, percentage, calculate_next_nag,
    businesstimedelta
)


def new_report(**kwargs):
    right_now = now()
    return Report(**{**dict(
        id=12345,
        title='a report',
        created_at=right_now,
        state='new',
        last_synced_at=right_now,
        is_eligible_for_bounty=True,
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


def test_calculate_next_nag_works_when_never_nagged():
    created_at = datetime(2017, 6, 19, 14, tzinfo=pytz.utc)
    next_nag_at = calculate_next_nag(created_at)
    assert businesstimedelta(created_at, next_nag_at).days == 45


def test_calculate_next_nag_works_when_nagged_once():
    created_at = datetime(2017, 6, 19, 14, tzinfo=pytz.utc)
    last_nagged_at = calculate_next_nag(created_at)
    next_nag_at = calculate_next_nag(created_at, last_nagged_at)
    assert businesstimedelta(created_at, next_nag_at).days == 68


def test_calculate_next_nag_works_when_nagged_a_ton():
    created_at = datetime(2017, 6, 19, 14, tzinfo=pytz.utc)
    last_nagged_at = None
    nag_days = []
    for _ in range(10):
        last_nagged_at = calculate_next_nag(created_at, last_nagged_at)
        nag_days.append(businesstimedelta(created_at, last_nagged_at).days)
    assert nag_days == [45, 68, 79, 85, 87, 88, 89, 90, 91, 92]


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


DEFAULT_STATS = {
    'triage_accuracy': 100,
    'false_negatives': 0,
    'triaged_within_one_day': 100,
}


@pytest.mark.django_db
def test_get_stats_returns_defaults_when_counts_are_zero():
    assert Report.get_stats() == DEFAULT_STATS


@pytest.mark.django_db
def test_get_stats_ignores_reports_ineligible_for_bounty():
    kwargs = dict(is_eligible_for_bounty=False)
    new_triaged_report(id=1, triage_days=5, **kwargs).save()
    new_triaged_report(id=2, is_false_negative=True, **kwargs).save()
    new_triaged_report(id=3, is_accurate=False, **kwargs).save()

    assert Report.get_stats() == DEFAULT_STATS


@pytest.mark.django_db
def test_singleton_metadata_works():
    right_now = now()

    meta = SingletonMetadata.load()
    assert meta.id == 1
    assert meta.last_synced_at is None

    meta.last_synced_at = right_now
    meta.save()

    meta = SingletonMetadata.load()
    assert meta.id == 1
    assert meta.last_synced_at == right_now
