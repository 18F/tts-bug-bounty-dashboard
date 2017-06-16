import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Max
from django.utils import timezone

from dashboard import h1
from dashboard.models import Report


class Command(BaseCommand):
    help = 'Synchronizes DB with hackerone.com'

    def handle(self, *args, **options):
        now = timezone.now()
        res = Report.objects.all().aggregate(Max('last_synced_at'))
        last_sync = res['last_synced_at__max']

        if last_sync is None:
            last_sync = datetime.datetime.min

        listing = h1.find_reports(last_activity_at__gt=last_sync)
        count = len(listing)
        records = "records" if count != 1 else "record"
        self.stdout.write(f"Synchronizing {count} {records} with H1.")
        for h1_report in listing:
            Report.objects.update_or_create(
                defaults=dict(
                    title=h1_report.title,
                    created_at=h1_report.created_at,
                    triaged_at=h1_report.triaged_at,
                    state=h1_report.state,
                    last_synced_at=now,
                ),
                id=h1_report.id
            )
        self.stdout.write("Done.")
