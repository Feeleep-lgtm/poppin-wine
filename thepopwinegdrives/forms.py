# thepopwinegdrives/forms.py
from django import forms
from .models import Script
from pathlib import Path

# Function to get the service account email from a local file
def get_service_account_email():
    # Use BASE_DIR to construct the path to the email file
    BASE_DIR = Path(__file__).resolve().parent.parent
    email_file_path = BASE_DIR / 'service-account-email.txt'
    
    try:
        with open(email_file_path, 'r') as file:
            email = file.read().strip()
    except FileNotFoundError:
        email = 'service-account@example.com'  # Default value or handle error as needed
    return email

# Form for running scripts
class RunScriptForm(forms.Form):
    script_id = forms.ModelChoiceField(queryset=Script.objects.all())

# Form for scraping a webpage
class ScrapeForm(forms.Form):
    url = forms.URLField(label='URL to Scrape', widget=forms.URLInput(attrs={'size': '40'}))

# Form for fetching books from a Google Drive folder
class FetchBooksForm(forms.Form):
    folder_link = forms.URLField(
        widget=forms.URLInput(attrs={'placeholder': 'Enter Google Drive folder link'}),
        label='Google Drive Folder Link'
    )
    service_account_email = get_service_account_email()

# Form for fetching content from a Google Drive file
class FetchFileContentForm(forms.Form):
    file_link = forms.URLField(
        widget=forms.URLInput(attrs={'placeholder': 'Enter Google Drive file link'}),
        label='Google Drive File Link'
    )
    service_account_email = get_service_account_email()
