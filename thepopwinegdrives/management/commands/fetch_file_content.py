from django.core.management.base import BaseCommand
from thepopwinegdrives.models import Book  # Use the Book model
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import fitz  # PyMuPDF
import docx
import os
from pathlib import Path
from datetime import datetime
import time
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetch and store content from a Google Drive file link'

    def add_arguments(self, parser):
        parser.add_argument('file_link', type=str, help='Google Drive file link')

    def handle(self, *args, **kwargs):
        file_link = kwargs['file_link']
        
        # Use BASE_DIR to construct the path to the credentials file
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        credentials_path = BASE_DIR / 'service-account-key.json'
        
        fetch_and_store_file_content(file_link, credentials_path)

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def fetch_and_store_file_content(file_link, credentials_path):
    # Parse the file ID from the share link
    if 'file/d/' in file_link:
        file_id = file_link.split('file/d/')[1].split('/')[0]
    elif 'document/d/' in file_link:
        file_id = file_link.split('document/d/')[1].split('/')[0]
    else:
        raise ValueError("Invalid file link format")
    
    # Authenticate and build the service
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=["https://www.googleapis.com/auth/drive"])
    service = build('drive', 'v3', credentials=creds)

    # Get file metadata
    file_metadata = service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
    file_name = file_metadata['name']
    mime_type = file_metadata['mimeType']

    # Download the file with exponential backoff
    file_path = f"/tmp/{file_name}"
    success = False
    attempt = 0
    while not success:
        try:
            if mime_type == 'application/pdf':
                request = service.files().get_media(fileId=file_id)
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or mime_type == 'text/plain':
                request = service.files().get_media(fileId=file_id)
            elif mime_type == 'application/vnd.google-apps.document':
                request = service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            else:
                raise ValueError("Unsupported file type")

            with open(file_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            success = True
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 403 and 'userRateLimitExceeded' in e.content.decode():
                attempt += 1
                if attempt > 5:
                    logger.error("Exceeded maximum retry attempts for file: %s", file_name)
                    return
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning("Rate limit exceeded. Retrying in %s seconds...", sleep_time)
                time.sleep(sleep_time)
            else:
                logger.error("An error occurred: %s", e)
                return

    # Extract text based on file type
    if mime_type == 'application/pdf':
        content = extract_text_from_pdf(file_path)
    elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        content = extract_text_from_docx(file_path)
    elif mime_type == 'text/plain':
        with open(file_path, 'r') as f:
            content = f.read()
    else:
            content = ""

    # Ensure content is not None
    if content is None:
        logger.error("Failed to extract content for file: %s", file_name)
        return
    # Create or update the book record
    Book.objects.update_or_create(
        title=file_name,
        defaults={
            'author': 'Unknown',  # Default author, adjust as needed
            'last_accessed': datetime.now(),
            'content': content
        }
    )
    
    # Remove the downloaded file
    os.remove(file_path)
