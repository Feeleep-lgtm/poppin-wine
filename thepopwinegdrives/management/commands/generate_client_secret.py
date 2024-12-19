from thepopwinegdrives.models import ClientApp
from django.core.management.base import BaseCommand

import secrets

CLIENT_NAME="POPPIN_CHAT_WP_TEST"
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Generate a random API key
        api_key = secrets.token_urlsafe(32)

        # Create a new ClientApp
        client_app = ClientApp.objects.create(name=CLIENT_NAME, api_key=api_key)
        # print(f"API Key: {client_app.api_key}")
        print(f"Client details \nClient name: : {client_app.name}\nApi Key : {client_app.api_key}")

