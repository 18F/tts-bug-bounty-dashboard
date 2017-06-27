from django.db import models
from django.contrib.auth.models import User

from . import dates

# These need to be copacetic w/ the HackerOne API, i.e. H1 should never
# give us asset IDs or types that are longer than these values.
H1_ASSET_ID_MAXLEN = 255
H1_ASSET_TYPE_MAXLEN = 255


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
    asset_identifier = models.CharField(max_length=H1_ASSET_ID_MAXLEN,
                                        null=True)
    asset_type = models.CharField(max_length=H1_ASSET_TYPE_MAXLEN,
                                  null=True)
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


class Product(models.Model):
    '''
    Represents one of our products, e.g. Federalist or login.gov.
    '''

    title = models.CharField(max_length=50)

    owner = models.ForeignKey(
        to=User,
        help_text=('Individual responsible for the product. Nags will '
                   'be sent to them if reports aren\'t closed.')
    )


class ProductAsset(models.Model):
    '''
    Represents an asset that is associated with a product.

    This is the primary mechanism through which reports are mapped to
    products and product owners.
    '''

    class Meta:
        unique_together = ("h1_asset_identifier", "h1_asset_type")
        index_together = list(unique_together)

    h1_asset_identifier = models.CharField(
        max_length=H1_ASSET_ID_MAXLEN,
        help_text=('The HackerOne asset identifier; it is probably a URL '
                   'of some sort, but it can also be the name of a '
                   'downloadable executable, an app store ID, or a variety '
                   'of other things depending on the asset type.'),
    )

    # We would supply a list of choices here, but HackerOne hasn't
    # documented them at the time of this writing (June 2017), so we won't.
    h1_asset_type = models.CharField(
        max_length=H1_ASSET_TYPE_MAXLEN,
        help_text=('The HackerOne asset type; can be URL, SOURCE_CODE, or '
                   'other values that are currently undocumented by H1.'),
    )

    product = models.ForeignKey(
        to=Product,
        help_text='The product this asset belongs to.',
        null=True,
    )
