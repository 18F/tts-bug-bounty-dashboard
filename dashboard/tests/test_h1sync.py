import datetime
import io
import pytest
import attr
from unittest import mock
from django.utils import timezone
from django.core.management import call_command
from h1.models import Report as H1Report

from .test_models import new_report
from ..models import SingletonMetadata, Report


is_datetime = attr.validators.instance_of(datetime.datetime)

_next_unique_id = 1


def make_unique_id():
    global _next_unique_id

    result = _next_unique_id
    _next_unique_id += 1
    return result


@attr.s
class FakeApiReport:
    '''
    A fake version of the Report object returned by the h1 package.
    '''

    id = attr.ib(
        default=attr.Factory(make_unique_id),
        validator=attr.validators.instance_of(int)
    )

    title = attr.ib(
        default='some report',
        validator=attr.validators.instance_of(str)
    )

    created_at = attr.ib(
        default=attr.Factory(timezone.now),
        validator=is_datetime
    )

    triaged_at = attr.ib(
        default=None,
        validator=attr.validators.optional(is_datetime)
    )

    state = attr.ib(
        default='new',
        validator=attr.validators.in_(H1Report.STATES)
    )


def call_h1sync(reports=None):
    if reports is None:
        reports = []
    with mock.patch('dashboard.h1.find_reports') as mock_find_reports:
        mock_find_reports.return_value = reports
        out = io.StringIO()
        call_command('h1sync', stdout=out)
        return out.getvalue(), mock_find_reports


@pytest.mark.django_db
def test_it_does_not_filter_by_last_activity_if_never_synced():
    output, mock_find = call_h1sync()
    mock_find.assert_called_once_with()
    assert 'Last sync' not in output


@pytest.mark.django_db
def test_it_updates_last_synced_at():
    assert SingletonMetadata.load().last_synced_at is None
    call_h1sync()
    assert SingletonMetadata.load().last_synced_at is not None


@pytest.mark.django_db
def test_it_filters_by_last_activity_if_previously_synced():
    now = timezone.now()
    meta = SingletonMetadata.load()
    meta.last_synced_at = now
    meta.save()
    output, mock_find = call_h1sync()
    mock_find.assert_called_once_with(last_activity_at__gt=now)
    assert 'Last sync' in output


@pytest.mark.django_db
def test_it_outputs_number_of_records_updated():
    output, _ = call_h1sync(reports=[])
    assert 'Synchronizing 0 records with HackerOne' in output

    output, _ = call_h1sync(reports=[FakeApiReport()])
    assert 'Synchronizing 1 record with HackerOne' in output

    output, _ = call_h1sync(reports=[FakeApiReport(), FakeApiReport()])
    assert 'Synchronizing 2 records with HackerOne' in output


@pytest.mark.django_db
def test_it_updates_reports_in_db():
    report = new_report(title='foo')
    report.is_false_negative = True
    report.save()

    call_h1sync(reports=[FakeApiReport(id=report.id, title='bar')])

    report.refresh_from_db()
    assert report.title == 'bar'
    assert report.is_false_negative


@pytest.mark.django_db
def test_it_creates_new_reports_in_db():
    call_h1sync(reports=[FakeApiReport(id=91, title='foo')])
    report = Report.objects.filter(id=91).first()
    assert report.title == 'foo'
