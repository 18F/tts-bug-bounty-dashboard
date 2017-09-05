import datetime
import pytest
import pytz
from django.utils.timezone import now

from .test_dates import create_dates_business_days_apart
from ..models import Report, SingletonMetadata


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
    created_at, triaged_at = create_dates_business_days_apart(triage_days)
    return new_report(
        created_at=created_at,
        triaged_at=triaged_at,
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

@pytest.mark.django_db
def test_save_sets_days_until_triage_to_value_if_closed():
    created_at, closed_at = create_dates_business_days_apart(1)
    report = new_report(created_at=created_at, closed_at=closed_at)
    report.save()
    assert report.days_until_triage == 1


@pytest.mark.django_db
def test_get_stats_reports_triage_accuracy():
    new_report(id=1, is_accurate=True).save()
    new_report(id=2, is_accurate=False).save()
    assert Report.get_stats()['triaged_accurately'] == 1


@pytest.mark.django_db
def test_get_stats_reports_false_negatives():
    new_report(id=1, is_false_negative=True).save()
    new_report(id=2, is_false_negative=False).save()
    assert Report.get_stats()['false_negatives'] == 1


@pytest.mark.django_db
def test_get_stats_reports_triaged_within_one_day():
    new_report(id=1).save()
    new_triaged_report(triage_days=1, id=2).save()
    new_triaged_report(triage_days=2, id=3).save()
    assert Report.get_stats()['triaged_within_one_day'] == 1


DEFAULT_STATS = {
    'count': 0,
    'triaged_accurately': 0,
    'false_negatives': 0,
    'triaged_within_one_day': 0,
}

@pytest.mark.django_db
def test_get_stats_returns_defaults_when_counts_are_zero():
    assert Report.get_stats() == DEFAULT_STATS

@pytest.mark.django_db
def test_get_stats_ignores_reports_ineligible_for_bounty():
    new_triaged_report(id=1, triage_days=4, is_eligible_for_bounty=False).save()
    new_triaged_report(id=2, is_false_negative=True, is_eligible_for_bounty=False).save()
    new_triaged_report(id=3, is_accurate=False, is_eligible_for_bounty=False).save()
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

@pytest.mark.django_db
def test_get_stats_by_month():

    # Make two tickets in September: one triaged on time, one not. Date
    # carefully chosen: a Monday, not Labor Day, to make the business day
    # calculation work out correctly.
    created_at = datetime.datetime(2017, 9, 11, 14, 0, tzinfo=pytz.utc)
    new_report(id=1, created_at=created_at, triaged_at=created_at + datetime.timedelta(days=1)).save()
    new_report(id=2, created_at=created_at, triaged_at=created_at + datetime.timedelta(days=2)).save()

    # And now two tickets in August, both triaged on time, similar criteria
    created_at = datetime.datetime(2017, 8, 7, 14, 0, tzinfo=pytz.utc)
    new_report(id=3, created_at=created_at, triaged_at=created_at + datetime.timedelta(days=1)).save()
    new_report(id=4, created_at=created_at, triaged_at=created_at + datetime.timedelta(days=1)).save()

    expected_stats = {
        datetime.date(2017, 8, 1): {
            'count': 2,
            'triaged_accurately': 2,
            'false_negatives': 0,
            'triaged_within_one_day': 2,
        },
        datetime.date(2017, 9, 1): {
            'count': 2,
            'triaged_accurately': 2,
            'false_negatives': 0,
            'triaged_within_one_day': 1,
        }
    }

    assert Report.get_stats_by_month() == expected_stats

@pytest.mark.django_db
def test_get_stats_by_month_different_contract_start_day():

    contract_start_day = 7

    # these two tickets are on two "sides" of a contract day, so we should get
    # two months out of the stats.
    d1 = datetime.datetime(2017, 9, 11, 14, 0, tzinfo=pytz.utc)
    new_report(id=1, created_at=d1, triaged_at=d1 + datetime.timedelta(days=1)).save()

    d2 = datetime.datetime(2017, 9, 4, 14, 0, tzinfo=pytz.utc)
    new_report(id=2, created_at=d2, triaged_at=d2 + datetime.timedelta(days=2)).save()

    expected_stats = {
        datetime.date(2017, 8, contract_start_day): {
            'count': 1,
            'triaged_accurately': 1,
            'false_negatives': 0,
            'triaged_within_one_day': 1,
        },
        datetime.date(2017, 9, contract_start_day): {
            'count': 1,
            'triaged_accurately': 1,
            'false_negatives': 0,
            'triaged_within_one_day': 1,
        }
    }

    assert Report.get_stats_by_month(contract_start_day) == expected_stats
