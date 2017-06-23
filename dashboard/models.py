import pytz
import datetime
from django.db import models
from businesstime import BusinessTime
from businesstime.holidays.usa import USFederalHolidays


# Number of business days we have to fix a security vulnerability.
SLA_DAYS = 90

# Days before SLA_DAYS we'll nag someone to attend to the vulnerability.
NAG_DAYS = [45, 22, 11, 5, 3, 2, 1]

# The timezone we base all "business day aware" date calculations on.
BUSINESS_TIMEZONE = 'US/Eastern'

_businesstime = BusinessTime(holidays=USFederalHolidays())


def percentage(n, d, default=0):
    if d == 0:
        return default
    return int((float(n) / float(d)) * 100.0)


def businesstimedelta(a, b):
    '''
    Calculate the timedelta between two timezone-aware datetimes.

    Note that due to the fact that the businesstime package doesn't currently
    accept timezone-aware datetimes, we need to convert them to
    timezone-naive ones first.

    For future reference, this issue has been filed at:

        https://github.com/seatgeek/businesstime/issues/18
    '''

    # https://stackoverflow.com/a/5452709
    est = pytz.timezone(BUSINESS_TIMEZONE)
    return _businesstime.businesstimedelta(
        a.astimezone(est).replace(tzinfo=None),
        b.astimezone(est).replace(tzinfo=None),
    )


def calculate_next_nag(created_at, last_nagged_at=None):
    '''
    Given the date/time a report was issued and the date/time we
    last nagged someone to attend to it (if any), calculate the date/time of
    the next nag.
    '''

    # Partly due to apparent limitations in the businesstime package,
    # this code is horrible.

    last_nag_day = 0
    if last_nagged_at is not None:
        last_nag_day = businesstimedelta(created_at, last_nagged_at).days

    nag_days_left = [
        SLA_DAYS - days for days in NAG_DAYS
        if SLA_DAYS - days > last_nag_day
    ]

    if nag_days_left:
        next_nag_day = nag_days_left[0]
    else:
        next_nag_day = last_nag_day + 1

    dt = created_at
    while True:
        dt += datetime.timedelta(hours=24)
        days_since_creation = businesstimedelta(created_at, dt).days
        if days_since_creation >= next_nag_day:
            return dt


class Report(models.Model):
    '''
    Represents a HackerOne report, along with our metadata.
    '''

    # These states are taken from:
    # https://api.hackerone.com/docs/v1#/reports
    STATES = (
        'new',
        'triaged',
        'needs-more-info',
        'resolved',
        'not-applicable',
        'informative',
        'duplicate',
        'spam',
    )

    H1_OWNED_FIELDS = (
        'title',
        'created_at',
        'triaged_at',
        'closed_at',
        'state',
        'is_eligible_for_bounty',
        'id',
    )

    # Data mirrored from h1
    title = models.TextField()
    created_at = models.DateTimeField()
    triaged_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    state = models.CharField(max_length=30, choices=[
        (name, name) for name in STATES
    ])
    is_eligible_for_bounty = models.NullBooleanField()
    id = models.PositiveIntegerField(primary_key=True)

    # Data we own/maintain
    is_accurate = models.BooleanField(
        default=True,
        help_text='Whether we agree with HackerOne\'s triage assessment.',
    )
    is_false_negative = models.BooleanField(
        default=False,
        help_text=('Whether HackerOne improperly classified the report '
                   'as invalid or duplicate.'),
    )
    days_until_triage = models.IntegerField(
        help_text=('Number of business days between a report being filed '
                   'and being triaged.'),
        blank=True,
        null=True,
    )
    last_nagged_at = models.DateTimeField(
        help_text=('When we last contacted the person ultimately responsible '
                   'for this report, encouraging them to pay attention to '
                   'it.'),
        blank=True,
        null=True
    )
    next_nag_at = models.DateTimeField(
        help_text=('When we should contact the person ultimately responsible '
                   'for this report, encouraging them to pay attention to '
                   'it.'),
        blank=True,
        null=True
    )
    last_synced_at = models.DateTimeField()

    def get_absolute_url(self):
        return f'https://hackerone.com/reports/{self.id}'

    def _set_days_until_triage(self):
        if self.created_at and self.triaged_at:
            self.days_until_triage = businesstimedelta(
                self.created_at,
                self.triaged_at
            ).days
        else:
            self.days_until_triage = None

    def _set_next_nag_at(self):
        if self.closed_at is None and self.is_eligible_for_bounty:
            self.next_nag_at = calculate_next_nag(
                self.created_at,
                self.last_nagged_at
            )
        else:
            self.next_nag_at = None

    def save(self, *args, **kwargs):
        self._set_days_until_triage()
        self._set_next_nag_at()
        return super().save(*args, **kwargs)

    @classmethod
    def get_stats(cls):
        reports = cls.objects.filter(is_eligible_for_bounty=True)
        count = reports.count()
        accurates = reports.filter(is_accurate=True).count()
        false_negatives = reports.filter(is_false_negative=True).count()
        triaged = reports.filter(days_until_triage__gte=0).count()
        triaged_within_one_day = reports.filter(
            days_until_triage__lte=1).count()

        return {
            'triage_accuracy': percentage(accurates, count, 100),
            'false_negatives': percentage(false_negatives, count, 0),
            'triaged_within_one_day': percentage(triaged_within_one_day,
                                                 triaged, 100)
        }


class SingletonMetadata(models.Model):
    '''
    A singleton model that stores metadata about the dashboard.
    '''

    SINGLETON_ID = 1

    id = models.PositiveIntegerField(primary_key=True)

    last_synced_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='When the dashboard was last synced with HackerOne.'
    )

    def save(self, *args, **kwargs):
        self.id = self.SINGLETON_ID
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(id=cls.SINGLETON_ID)[0]
