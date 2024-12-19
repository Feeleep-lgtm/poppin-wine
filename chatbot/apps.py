from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

# def create_chroma_db(sender, **kwargs):
#     try:
#         call_command('create_chroma_db')
#     except Exception as e:
#         logger.error(f"Error creating Chroma database: {e}")

class ChatbotConfig(AppConfig):
    name = 'chatbot'

    # def ready(self):
    #     post_migrate.connect(create_chroma_db, sender=self)
