from django.db import models
from django.contrib.postgres.fields import HStoreField

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
        'disclosed_at',
        'state',
        'asset_identifier',
        'asset_type',
        'is_eligible_for_bounty',
        'issue_tracker_reference_url',
        'weakness',
        'id',
    )

    # Data mirrored from h1
    title = models.TextField()
    created_at = models.DateTimeField()
    triaged_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    disclosed_at = models.DateTimeField(blank=True, null=True)
    state = models.CharField(max_length=30, choices=[
        (name, name) for name in STATES
    ])
    asset_identifier = models.CharField(max_length=255, null=True)
    asset_type = models.CharField(max_length=255, null=True)

    # In the H1 API, this is an object with an ID and a few other fields.
    # However, I don't much see the point in that, but if I'm wrong this
    # could be broken out to an FK(Weakness) in the future.
    weakness = models.CharField(max_length=500, blank=True)

    is_eligible_for_bounty = models.NullBooleanField()
    issue_tracker_reference_url = models.URLField(max_length=500, blank=True)
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
    sla_triaged_at = models.DateTimeField(
        blank=True, null=True,
        help_text=("Date when we consider the issue triaged for SLA purposes, "
                   "which may or may not agree with triaged_at.")
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
        # close date as the date that counts as "triaged". Also, some issues
        # may have override triage dates in the sla_triaged_at field, and that
        # trumps ther other fields if it exists.

        if self.sla_triaged_at:
            triage_date = self.sla_triaged_at
        elif self.triaged_at:
            triage_date = self.triaged_at
        elif self.closed_at:
            triage_date = self.closed_at
        else:
            triage_date = None

        if triage_date:
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
        triaged_within_one_day = reports.filter(days_until_triage__lte=1).count()

        return {
            'count': count,
            'triaged_accurately': accurates,
            'false_negatives': false_negatives,
            'triaged_within_one_day': triaged_within_one_day,
        }

    @classmethod
    def get_stats_by_month(cls, contract_month_start_day=1):
        """
        Get SLA stats, broken down by calendar month.
        """
        # I could do this in SQL with date_trunc, but eventually this'll need
        # to be contract-month, so like the 7th-7th or something, which AFAIK
        # can't be done in SQL (and certainly not in Django). So just do this
        # by hand. There are only a few hundred reports/month right now, so this
        # should be OK.
        stats_by_month = {}

        reports = cls.objects.filter(is_eligible_for_bounty=True, days_until_triage__gte=0)
        for report in reports:
            first_day, last_day = dates.contract_month(report.created_at, contract_month_start_day)
            if first_day not in stats_by_month:
                stats_by_month[first_day] = {
                    'count': 0,
                    'triaged_accurately': 0,
                    'false_negatives': 0,
                    'triaged_within_one_day': 0,
                    'last_day': last_day,

                }

            stats_by_month[first_day]['count'] += 1
            stats_by_month[first_day]['triaged_accurately'] += report.is_accurate
            stats_by_month[first_day]['false_negatives'] += report.is_false_negative
            if report.days_until_triage <= 1:
                stats_by_month[first_day]['triaged_within_one_day'] += 1

        return stats_by_month


class Bounty(models.Model):
    '''
    A bounty awarded on a Report.

    See https://api.hackerone.com/docs/v1#bounty
    '''
    id = models.PositiveIntegerField(primary_key=True)
    report = models.ForeignKey(Report, related_name="bounties")
    amount = models.DecimalField(max_digits=8, decimal_places=2, help_text="USD")
    bonus = models.DecimalField(max_digits=8, decimal_places=2, help_text="USD", blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        verbose_name = "bounty"
        verbose_name_plural = "bounties"

    def __str__(self):
        return f"${self.amount} + ${self.bonus}" if self.bonus else f"${self.amount}"


class Activity(models.Model):
    """
    Represents an action performed on a report.

    See https://api.hackerone.com/docs/v1#activity

    HackerOne's API represents these with a bunch of different object types
    (e.g. ActivityAgreedOnGoingPublic, ActivityComment, etc). Since these have
    mostly-the-same fields, and since we don't want to have to update our
    database as new activity types get added, we represent this here with a
    single model. We'll use hstore to store the fields that different fields
    on each model.
    """
    id = models.PositiveIntegerField(primary_key=True)
    report = models.ForeignKey(Report, related_name="activities")
    type = models.CharField(max_length=150)
    created_at = models.DateTimeField()
    attributes = HStoreField(default=dict)

    class Meta:
        verbose_name = "activity"
        verbose_name_plural = "activities"
        ordering = ["created_at"]

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
