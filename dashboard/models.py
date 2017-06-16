from django.db import models
from workdays import networkdays
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
        help_text='Whether we agree with Hacker One\'s triage assessment.',
    )
    is_false_negative = models.BooleanField(
        default=False,
        help_text=('Whether Hacker One improperly classified the report '
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
            self.days_until_triage = networkdays(
                self.created_at,
                self.triaged_at,
                # TODO: Add list of federal holidays.
                holidays=[],
            )
        else:
            self.days_until_triage = None
        return super().save(*args, **kwargs)
