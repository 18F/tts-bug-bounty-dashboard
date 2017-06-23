from django.db import models

from . import dates


def percentage(n, d, default=0):
    if d == 0:
        return default
    return int((float(n) / float(d)) * 100.0)


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
            self.days_until_triage = dates.businesstimedelta(
                self.created_at,
                self.triaged_at
            ).days
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
