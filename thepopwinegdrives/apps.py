# from django.apps import AppConfig


# class ThepopwinegdrivesConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "thepopwinegdrives"
# thepopwinegdrives/apps.py

from django.apps import AppConfig
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

class ThePopWineGdrivesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'thepopwinegdrives'

    # def ready(self):
    #     # This will run the create_chroma_db command when the app is ready
    #     try:
    #         logger.info("Starting to populate ChromaDB...")
    #         call_command('create_chroma_db')
    #         # logger.info("ChromaDB population completed.")
    #     except Exception as e:
    #         logger.error("An error occurred while populating ChromaDB.", exc_info=True)
