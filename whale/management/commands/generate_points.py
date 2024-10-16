from django.core.management.base import BaseCommand
from whale.views import generate_interesting_points_subprocess

class Command(BaseCommand):
    help = "Runs the generate_interesting_points.py script as a subprocess."

    def add_arguments(self, parser):
        parser.add_argument('--input-file',
                            type=str,
                            help="GeoTIFF to be exploited")
        parser.add_argument('--output-file',
                            type=str,
                            help="Output GeoJSON file")
        parser.add_argument('--method',
                            type=str,
                            default='big_window',
                            help="Method (Default: Big Window)")
        parser.add_argument('--difference',
                            type=str,
                            default='20',
                            help="Difference (Default: 20)")

    def handle(self, *args, **options):
        input_file = options['input_file']
        output_file = options['output_file']
        method = options['method']
        difference = options['difference']
        
        self.stdout.write(self.style.SUCCESS(f"Starting the subprocess to generate interesting points..."))
        self.stdout.write(self.style.SUCCESS(f"\trunning using file: {input_file}, output file: {output_file}"))
        
        generate_interesting_points_subprocess(input_file, output_file, method, difference)
        
        self.stdout.write(self.style.SUCCESS(f"Subprocess execution completed"))