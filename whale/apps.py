from django.apps import AppConfig
from django.core.management import call_command


class WhaleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'whale'

    def read(self):
        try:
            subprocess.run(['git', 'config', '--global', 'http.schannelCheckRevoke', 'false'], check=True)
            subprocess.run(['git', 'config', '--global', 'http.sslBackend', 'openssl'], check=True)
            call_command('sync_repo')
        except subprocess.CalledProcessError as e:
            print(f"Failed to set Git configuration: {e}")