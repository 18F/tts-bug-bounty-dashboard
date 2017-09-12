from collections import defaultdict
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from h1.client import HackerOneClient

class Command(BaseCommand):
    help = 'Report on user/group differences between multiple programs'

    def handle(self, *args, **kwargs):
        program_list = list(self.find_programs())
        if len(program_list) < 2:
            raise CommandError("Only works with multiple programs")

        self.report_on_differences(program_list, 'groups', lambda i: i['attributes']['name'])
        self.stdout.write('')
        self.report_on_differences(program_list, 'members',
                                   lambda i: i['relationships']['user']['data']['attributes']['username'])

        self.stdout.write('')
        self.report_on_perm_differences(program_list)

    def find_programs(self):
        for program in settings.H1_PROGRAMS:
            client = HackerOneClient(program.api_username, program.api_password)
            resp = client.request_json('/me/programs')
            program_ids = (p['id'] for p in resp['data'])
            for program_id in program_ids:
                yield client.request_json(f'/programs/{program_id}')

    def report_on_differences(self, program_list, rel_name, name_getter):
        all_items = set()
        items_by_program = defaultdict(set)

        for program in program_list:
            item_names = [name_getter(i) for i in program['data']['relationships'][rel_name]['data']]
            all_items.update(item_names)
            items_by_program[program['data']['attributes']['handle']].update(item_names)

        for program_name, program_items in items_by_program.items():
            missing = all_items.difference(items_by_program[program_name])
            if missing:
                missing_names = ", ".join(missing)
                self.stdout.write(f"Missing {rel_name} from {program_name}: {missing_names}")

    def report_on_perm_differences(self, program_list):
        perms = defaultdict(dict)

        for program in program_list:
            program_name = program['data']['attributes']['handle']
            for member in program['data']['relationships']['members']['data']:
                username = member['relationships']['user']['data']['attributes']['username']
                permissions = member['attributes']['permissions']
                perms[username][program_name] = set(permissions)

        for user in perms:
            handled = False
            for program in perms[user]:
                other_programs = set(perms[user].keys()) - set([program])
                for other_program in other_programs:
                    if perms[user][program] != perms[user][other_program]:
                        self.stdout.write(f'Mismatching perms for {user}:')
                        self.stdout.write(f'    {program}: {perms[user][program]}')
                        self.stdout.write(f'    {other_program}: {perms[user][other_program]}')
                        handled = True
                if handled:
                    break
