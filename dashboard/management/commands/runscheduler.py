import time
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Runs the scheduler process'

    def run_cmd(self, cmd, *args, **options):
        self.stdout.write(f'Running "manage.py {cmd}".')
        call_command(cmd, *args, **options)

    def sleep(self, seconds):
        self.stdout.write(f'Waiting {seconds} seconds.')
        time.sleep(seconds)

    def handle(self, *args, **options):
        while True:
            self.run_cmd('h1sync')
            self.sleep(60)
