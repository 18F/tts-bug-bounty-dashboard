import pytz
from django.db import models
from businesstime import BusinessTime
from businesstime.holidays.usa import USFederalHolidays
from h1.models import Report as H1Report


def percentage(n, d, default=0):
    if d == 0:
        return default
    return int((float(n) / float(d)) * 100.0)


class Report(models.Model):
    '''
    Represents a HackerOne report, along with our metadata.
    '''

    # Data mirrored from h1
    title = models.TextField()
    created_at = models.DateTimeField()
    triaged_at = models.DateTimeField(blank=True, null=True)
    state = models.CharField(max_length=30, choices=[
        (name, name) for name in H1Report.STATES
    ])
    is_eligible_for_bounty = models.NullBooleanField()
    id = models.PositiveIntegerField(primary_key=True)

    H1_OWNED_FIELDS = (
        'title',
        'created_at',
        'triaged_at',
        'state',
        'id',
    )

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
    last_synced_at = models.DateTimeField()

    def get_absolute_url(self):
        return f'https://hackerone.com/reports/{self.id}'

    def save(self, *args, **kwargs):
        if self.created_at and self.triaged_at:
            bt = BusinessTime(holidays=USFederalHolidays())
            # https://stackoverflow.com/a/5452709
            est = pytz.timezone('US/Eastern')
            self.days_until_triage = bt.businesstimedelta(
                self.created_at.astimezone(est).replace(tzinfo=None),
                self.triaged_at.astimezone(est).replace(tzinfo=None),
            ).days
        else:
            self.days_until_triage = None
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
