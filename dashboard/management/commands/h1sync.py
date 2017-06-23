from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard import h1
from dashboard.models import Report, SingletonMetadata


class Command(BaseCommand):
    help = 'Synchronizes DB with hackerone.com'

    def handle(self, *args, **options):
        now = timezone.now()
        metadata = SingletonMetadata.load()
        kwargs = {}

        if metadata.last_synced_at is not None:
            self.stdout.write(f"Last sync was at {metadata.last_synced_at}.")
            kwargs['last_activity_at__gt'] = metadata.last_synced_at

        listing = h1.find_reports(**kwargs)
        count = len(listing)
        records = "records" if count != 1 else "record"
        self.stdout.write(f"Synchronizing {count} {records} with HackerOne.")
        for h1_report in listing:
            scope = h1_report.structured_scope
            if not (scope and scope.eligible_for_bounty):
                self.stdout.write(
                    f"Skipping #{h1_report.id}, it's not eligible for bounty."
                )
                continue
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
        metadata.last_synced_at = now
        metadata.save()
        self.stdout.write("Done.")
