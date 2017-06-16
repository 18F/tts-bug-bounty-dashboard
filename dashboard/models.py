from django.db import models
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
    is_false_positive = models.BooleanField(
        default=False,
        help_text=('Whether Hacker One improperly classified the report '
                   'as invalid or duplicate.'),
    )
    last_synced_at = models.DateTimeField()

    def get_absolute_url(self):
        return f'https://hackerone.com/reports/{self.id}'
