
"""
Django Application Configuration for Animal app.

This class extends Django's AppConfig to provide custom configuration for the Animal application.
It includes functionality to configure Git settings and synchronize repositories.

Methods:
    read(): Configures Git SSL settings and syncs repositories
        - Disables SSL certificate revocation checking
        - Sets SSL backend to OpenSSL
        - Calls sync_repo management command
        
Raises:
    subprocess.CalledProcessError: If Git configuration commands fail
"""

from django.apps import AppConfig
from django.core.management import call_command
import subprocess

class AnimalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'animal'

    def read(self):
        try:
            subprocess.run(['git', 'config', '--global', 'http.schannelCheckRevoke', 'false'], check=True)
            subprocess.run(['git', 'config', '--global', 'http.sslBackend', 'openssl'], check=True)
            call_command('sync_repo')
        except subprocess.CalledProcessError as e:
            print(f"Failed to set Git configuration: {e}")