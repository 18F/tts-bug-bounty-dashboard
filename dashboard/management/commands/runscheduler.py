import time
import logging
from django.core.management import call_command
from django.core.management.base import BaseCommand


logger = logging.getLogger('scheduler')


class Command(BaseCommand):
    help = 'Runs the scheduler process'

    def run_cmd(self, cmd, *args, **options):
        cmdline = f'manage.py {cmd}'
        logger.info(f'Running "{cmdline}".')
        try:
            call_command(cmd, *args, **options)
        except Exception as e:
            logger.exception(f'An error occurred when running "{cmdline}".')

    def sleep(self, seconds):
        logger.info(f'Waiting {seconds} seconds.')
        time.sleep(seconds)

    def handle(self, *args, **options):
        while True:
            self.run_cmd('h1sync')
            self.sleep(600)
