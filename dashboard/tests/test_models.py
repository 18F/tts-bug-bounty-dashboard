import datetime
import pytest
import pytz
from decimal import Decimal
from django.utils.timezone import now

from .test_dates import create_dates_business_days_apart
from ..models import Report, Bounty, Activity, SingletonMetadata


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
        sla_triaged_at=triaged_at,
        **kwargs
    )


def test_get_absolute_url_works():
    r = new_report(id=4567)
    assert r.get_absolute_url() == 'https://hackerone.com/reports/4567'


@pytest.mark.django_db
def test_save_sets_days_until_triage_to_none_if_untriaged():
    r = new_report(sla_triaged_at=None)
    r.save()
    assert r.days_until_triage is None


@pytest.mark.django_db
def test_save_sets_days_until_triage_to_value_if_triaged():
    r = new_triaged_report(triage_days=1)
    r.save()
    assert r.days_until_triage == 1


@pytest.mark.django_db
def test_get_stats_reports_triage_accuracy():
    new_triaged_report(id=1, is_accurate=True, triage_days=1).save()
    new_triaged_report(id=2, is_accurate=False, triage_days=1).save()
    assert Report.get_stats()['totals']['triaged_accurately'] == 1


@pytest.mark.django_db
def test_get_stats_reports_false_negatives():
    new_triaged_report(id=1, is_false_negative=True, triage_days=1).save()
    new_triaged_report(id=2, is_false_negative=False, triage_days=1).save()
    assert Report.get_stats()['totals']['false_negatives'] == 1


@pytest.mark.django_db
def test_get_stats_reports_triaged_within_one_day():
    new_report(id=1).save()
    new_triaged_report(triage_days=1, id=2).save()
    new_triaged_report(triage_days=2, id=3).save()
    assert Report.get_stats()['totals']['triaged_within_one_day'] == 1


DEFAULT_STATS = {
    'count': 0,
    'triaged_accurately': 0,
    'false_negatives': 0,
    'triaged_within_one_day': 0,
}

@pytest.mark.django_db
def test_get_stats_returns_defaults_when_counts_are_zero():
    assert Report.get_stats()['totals'] == DEFAULT_STATS

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
def test_monthly_stats():

    # Make two tickets in September: one triaged on time, one not. Date
    # carefully chosen: a Monday, not Labor Day, to make the business day
    # calculation work out correctly.
    created_at = datetime.datetime(2017, 9, 11, 14, 0, tzinfo=pytz.utc)
    new_report(id=1, created_at=created_at, sla_triaged_at=created_at + datetime.timedelta(days=1)).save()
    new_report(id=2, created_at=created_at, sla_triaged_at=created_at + datetime.timedelta(days=2)).save()

    # And now two tickets in August, both triaged on time, similar criteria
    created_at = datetime.datetime(2017, 8, 7, 14, 0, tzinfo=pytz.utc)
    new_report(id=3, created_at=created_at, sla_triaged_at=created_at + datetime.timedelta(days=1)).save()
    new_report(id=4, created_at=created_at, sla_triaged_at=created_at + datetime.timedelta(days=1)).save()

    expected_stats = {
        datetime.date(2017, 8, 1): {
            'count': 2,
            'triaged_accurately': 2,
            'false_negatives': 0,
            'triaged_within_one_day': 2,
            'last_day': datetime.date(2017, 8, 31)
        },
        datetime.date(2017, 9, 1): {
            'count': 2,
            'triaged_accurately': 2,
            'false_negatives': 0,
            'triaged_within_one_day': 1,
            'last_day': datetime.date(2017, 9, 30)
        },
        'totals': {
            'count': 4,
            'triaged_accurately': 4,
            'false_negatives': 0,
            'triaged_within_one_day': 3,
        }
    }

    assert Report.get_stats() == expected_stats

@pytest.mark.django_db
def test_monthly_stats_different_contract_start_day():

    contract_start_day = 7

    # these two tickets are on two "sides" of a contract day, so we should get
    # two months out of the stats.
    d1 = datetime.datetime(2017, 9, 11, 14, 0, tzinfo=pytz.utc)
    new_report(id=1, created_at=d1, sla_triaged_at=d1 + datetime.timedelta(days=1)).save()

    d2 = datetime.datetime(2017, 9, 4, 14, 0, tzinfo=pytz.utc)
    new_report(id=2, created_at=d2, sla_triaged_at=d2 + datetime.timedelta(days=2)).save()

    expected_stats = {
        datetime.date(2017, 8, contract_start_day): {
            'count': 1,
            'triaged_accurately': 1,
            'false_negatives': 0,
            'triaged_within_one_day': 1,
            'last_day': datetime.date(2017, 9, contract_start_day - 1)
        },
        datetime.date(2017, 9, contract_start_day): {
            'count': 1,
            'triaged_accurately': 1,
            'false_negatives': 0,
            'triaged_within_one_day': 1,
            'last_day': datetime.date(2017, 10, contract_start_day - 1)
        },
        'totals': {
            'count': 2,
            'triaged_accurately': 2,
            'false_negatives': 0,
            'triaged_within_one_day': 2,
        }
    }

    assert Report.get_stats(contract_start_day) == expected_stats

@pytest.mark.django_db
def test_bounty_str_no_bonus():
    r = new_report()
    b = Bounty(report=r, created_at=now(), amount=Decimal("50.00"))
    assert str(b) == "$50.00"

@pytest.mark.django_db
def test_bounty_str_with_bonus():
    r = new_report()
    b = Bounty(report=r, created_at=now(), amount=Decimal("50.00"), bonus=Decimal("5.00"))
    assert str(b) == "$50.00 + $5.00"

def test_activity_actor():
    a = Activity(attributes={'H1_actor': 'joe', 'H1_actor_type': 'user'})
    assert a.actor == "<user: joe>"

def test_activity_actor_missing():
    a = Activity()
    assert a.actor is None

def test_activity_group():
    a = Activity(attributes={'H1_group': '18f'})
    assert a.group == '18f'

def test_activity_group_missing():
    a = Activity()
    assert a.group is None

@pytest.mark.django_db
def test_activity_sets_sla_triaged_at():
    r = new_report()
    r.save()
    assert r.sla_triaged_at is None

    # An activity that shouldn't update sla_triaged_at
    d1 = now()
    r.activities.create(id=1, type='activity-comment', created_at=d1)
    assert r.sla_triaged_at is None

    # And now one that should
    d2 = d1 + datetime.timedelta(hours=3)
    r.activities.create(id=2, type='activity-bug-not-applicable', created_at=d2)
    assert r.sla_triaged_at == d2

    # And now another aciivity that would update the date, if it wasn't already set
    d3 = d2 + datetime.timedelta(hours=3)
    r.activities.create(id=3, type='activity-bug-resolved', created_at=d3)
    assert r.sla_triaged_at == d2

def create_activity_and_assign_to_group(group_name):
    report = new_report()
    report.save()

    date = now()
    report.activities.create(id=1,
                             type='activity-group-assigned-to-bug',
                             created_at=date,
                             attributes={'H1_group': group_name})
    return date, report

@pytest.mark.django_db
def test_assign_to_group_sets_sla_triaged_at():
    """Assigning to a group sets sla_triaged_at"""
    date, report = create_activity_and_assign_to_group("TTS")
    assert report.sla_triaged_at == date

@pytest.mark.django_db
def test_assign_to_h1_group_does_not_set_sla_triaged_at():
    """
    Assigning to a HackerOne group - indicated by an "H1-" prefix -- does not
    set sla_triaged_at
    """
    date, report = create_activity_and_assign_to_group("H1-triage")
    assert report.sla_triaged_at is None
