from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard import h1
from dashboard.models import Report, SingletonMetadata


class Command(BaseCommand):
    help = 'Synchronizes DB with hackerone.com'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            dest='all',
            action='store_true',
            default=False,
            help='Re-sync all data, ignoring last sync date',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        metadata = SingletonMetadata.load()
        kwargs = {}

        if metadata.last_synced_at is not None and not options['all']:
            self.stdout.write(f"Last sync was at {metadata.last_synced_at}.")
            kwargs['last_activity_at__gt'] = metadata.last_synced_at

        listing = h1.find_reports(**kwargs)
        count = 0
        for h1_report in listing:
            self.stdout.write(f"Synchronizing #{h1_report.id}.")
            scope = h1_report.structured_scope

            # Create or update the report
            report, created = Report.objects.update_or_create(
                defaults=dict(
                    title=h1_report.title,
                    created_at=h1_report.created_at,
                    triaged_at=h1_report.triaged_at,
                    closed_at=h1_report.closed_at,
                    disclosed_at=h1_report.disclosed_at,
                    state=h1_report.state,
                    issue_tracker_reference_url=h1_report.issue_tracker_reference_url or "",
                    weakness=h1_report.weakness.name if h1_report.weakness else "",
                    asset_identifier=scope and scope.asset_identifier,
                    asset_type=scope and scope.asset_type,
                    is_eligible_for_bounty=scope and scope.eligible_for_bounty,
                    last_synced_at=now,
                ),
                id=h1_report.id
            )

            # If there are awarded bounties, create/update them
            for h1_bounty in h1_report.bounties:
                report.bounties.update_or_create(id=h1_bounty.id, defaults=dict(
                    amount=h1_bounty.amount,
                    bonus=h1_bounty.bonus_amount,
                    created_at=h1_bounty.created_at,
                ))

            # Sync activities
            # The H1 API doesn't return activities on a search, which is what
            # find_reports() does, so we have to re-fetch the resource. This
            # slows things down, grrr, but... oh well.
            h1_report._fetch_canonical()
            for h1_activity in h1_report.activities:
                report.activities.update_or_create(id=h1_activity.id, defaults=dict(
                    type=h1_activity.TYPE,
                    created_at=h1_activity.created_at,
                    attributes=h1_activity.raw_data["attributes"]
                ))

            count += 1
        records = "records" if count != 1 else "record"
        self.stdout.write(f"Synchronized {count} {records} with HackerOne.")

        metadata.last_synced_at = now
        metadata.save()
        self.stdout.write("Done.")
