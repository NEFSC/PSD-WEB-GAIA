from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "This is a test function."

    def add_arguments(self, parser):
        parser.add_argument("trial_text",
                            type=str,
                            help="Test argument")

    def handle(self, *args, **options):
        # statement = options.get('test_arg')
        # self.stdout.write(self.style.SUCCESS('This is success text! Yay!'))
        # self.stdout.write(self.style.SUCCESS(f'This is your statement: {statement}'))
        # print(f"Test command executed!")
        # print(f"\tOptions received: {options}")
        statement = options['test']
        for test in args:
            self.stdout.write(self.style.SUCCESS(f'This is your statement: {test}'))
