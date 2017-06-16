import pytz
from django.db import models
from businesstime import BusinessTime
from businesstime.holidays.usa import USFederalHolidays
from h1.models import Report as H1Report


class Report(models.Model):
    # Data mirrored from h1
    title = models.TextField()
    created_at = models.DateTimeField()
    triaged_at = models.DateTimeField(blank=True, null=True)
    state = models.CharField(max_length=30, choices=[
        (name, name) for name in H1Report.STATES
    ])
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
            est=pytz.timezone('US/Eastern')
            self.days_until_triage = bt.businesstimedelta(
                self.created_at.astimezone(est).replace(tzinfo=None),
                self.triaged_at.astimezone(est).replace(tzinfo=None),
            ).days
        else:
            self.days_until_triage = None
        return super().save(*args, **kwargs)
