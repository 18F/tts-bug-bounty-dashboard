import datetime
from django.db import models

from . import dates


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
        'asset_identifier',
        'asset_type',
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
    asset_identifier = models.CharField(max_length=255, null=True)
    asset_type = models.CharField(max_length=255, null=True)
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
        # For SLA metrics, we want to know how many business days from opening
        # until triage. We can't just go by the triage date, though, because
        # some issues get moved directly from new to closed - for example,
        # issues marked as duplicate. So use either the triage date or the
        # close date as the date that counts as "triaged"

        triage_date = self.triaged_at or self.closed_at

        if self.created_at and triage_date:
            self.days_until_triage = dates.businesstimedelta(self.created_at, triage_date).days
        else:
            self.days_until_triage = None

    def _set_next_nag_at(self):
        if self.closed_at is None and self.is_eligible_for_bounty:
            self.next_nag_at = dates.calculate_next_nag(
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
        """
        Get aggregate SLA stats, all time.
        """
        reports = cls.objects.filter(is_eligible_for_bounty=True)
        count = reports.count()
        accurates = reports.filter(is_accurate=True).count()
        false_negatives = reports.filter(is_false_negative=True).count()
        triaged = reports.filter(days_until_triage__gte=0).count()
        triaged_within_one_day = reports.filter(
            days_until_triage__lte=1).count()

        return {
            'count': count,
            'triaged_accurately': accurates,
            'false_negatives': false_negatives,
            'triaged_within_one_day': triaged_within_one_day,
        }

    @classmethod
    def get_stats_by_month(cls):
        """
        Get SLA stats, broken down by calendar month.
        """
        # I could do this in SQL with date_trunc, but eventually this'll need
        # to be contract-month, so like the 7th-7th or something, which AFAIK
        # can't be done in SQL (and certainly not in Django). So just do this
        # by hand. There are only a few hundred reports/month right now, so this
        # should be OK.
        stats_by_month = {}

        reports = cls.objects.filter(is_eligible_for_bounty=True)
        for report in reports:
            month = datetime.date(report.created_at.year, report.created_at.month, 1)
            if month not in stats_by_month:
                stats_by_month[month] = {
                    'count': 0,
                    'triaged_accurately': 0,
                    'false_negatives': 0,
                    'triaged_within_one_day': 0,
                }

            stats_by_month[month]['count'] += 1
            stats_by_month[month]['triaged_accurately'] += report.is_accurate
            stats_by_month[month]['false_negatives'] += report.is_false_negative
            if report.days_until_triage <= 1:
                stats_by_month[month]['triaged_within_one_day'] += 1

        return stats_by_month
                

class SingletonMetadata(models.Model):
    '''
    A singleton model that stores metadata about the dashboard.
    '''

    class Meta:
        verbose_name = "dashboard settings"
        verbose_name_plural = "dashboard settings"

    SINGLETON_ID = 1

    id = models.PositiveIntegerField(primary_key=True)

    last_synced_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=('When the dashboard was last synced with HackerOne. '
                   'This field generally is not intended for editing, but '
                   'you can clear it to ensure that the next scheduled '
                   'sync refreshes all data, which can be useful if the '
                   'dashboard somehow becomes out-of-sync with HackerOne.')
    )

    def save(self, *args, **kwargs):
        self.id = self.SINGLETON_ID
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(id=cls.SINGLETON_ID)[0]
