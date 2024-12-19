from celery import shared_task
from .management.commands.fetch_books import fetch_and_update_books
from datetime import date
from pathlib import Path

@shared_task
def periodic_fetch_and_update_books():
    share_link = 'https://drive.google.com/drive/folders/10X_S08jj62hkqsDFmX7xp7zFNJByvQj-?usp=sharing'
    BASE_DIR = Path(__file__).resolve().parent.parent
    credentials_path = BASE_DIR / 'service-account-key.json'
    fetch_and_update_books(share_link, credentials_path)
