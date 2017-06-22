import time
import logging
from django.core.management import call_command
from django.core.management.base import BaseCommand

from . import h1sync


logger = logging.getLogger('scheduler')


class Command(BaseCommand):
    help = 'Runs the scheduler process'

    def run_cmd(self, cmd, *args, **options):
        cmdname = cmd.__module__.split('.')[-1]
        cmdline = f'manage.py {cmdname}'
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
            self.run_cmd(h1sync.Command())
            self.sleep(60)
