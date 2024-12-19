#thepopwinegdrives/views.py
from django import forms
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status  # Import status module
from rest_framework import serializers
from rest_framework.parsers import JSONParser
from bs4 import BeautifulSoup
import requests
from .models import ScrapedContent, Book
from .serializers import BookSerializer
from django.http import HttpResponse
from django.core.management import call_command 
from django.contrib import messages
from django.contrib import admin 
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
        email = email_file_path  # Default value or handle error as needed
    return email

def home(request):
    return HttpResponse("Welcome to the API Home")

class BookListCreate(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

class ScrapeWebpageSerializer(serializers.Serializer):
    url = serializers.URLField()

class ScrapeWebpageView(APIView):
    parser_classes = [JSONParser]
    serializer_class = ScrapeWebpageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            url = serializer.validated_data['url']
            title, content = scrape_webpage(url)
            
            # Save the scraped content to the database
            ScrapedContent.objects.create(url=url, title=title, content=content)

            return Response({"title": title, "content": content}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def scrape_webpage(url):
    """
    Scrape contents of a web page and return the title and content.
    """
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Initialize BeautifulSoup to parse the content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract text from the BeautifulSoup object
    title = soup.title.string if soup.title else url
    text = soup.get_text(separator='\n', strip=True)
    
    # Return the title and content
    return title, text

class AggregatedContentView(APIView):
    def get(self, request, *args, **kwargs):
        books = Book.objects.all()
        scraped_contents = ScrapedContent.objects.all()
        aggregated_content = "\n".join(book.content for book in books if book.content)
        aggregated_content += "\n".join(scraped_content.content for scraped_content in scraped_contents if scraped_content.content)
        return Response({'aggregated_content': aggregated_content}, status=status.HTTP_200_OK)

class FetchBooksForm(forms.Form):
    folder_link = forms.URLField(widget=forms.URLInput(attrs={'placeholder': 'Enter Google Drive folder link'}))
    service_account_email = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly', 'value': get_service_account_email()}))

class FetchFileContentForm(forms.Form):
    file_link = forms.URLField(widget=forms.URLInput(attrs={'placeholder': 'Enter Google Drive file link'}))
    service_account_email = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly', 'value': get_service_account_email()}))

def fetch_books_view(request):
    if request.method == 'POST':
        form = FetchBooksForm(request.POST)
        if form.is_valid():
            folder_link = form.cleaned_data['folder_link']
            try:
                call_command('fetch_books', folder_link)
                messages.success(request, 'Books have been successfully fetched from the folder link.')
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
            return redirect('admin:thepopwinegdrives_book_changelist')
    else:
        form = FetchBooksForm()
    context = dict(
        admin.site.each_context(request),
        form=form,
        title='Fetch Books',
    )
    return render(request, 'admin/fetch_books_form.html', context)

def fetch_file_content_view(request):
    if request.method == 'POST':
        form = FetchFileContentForm(request.POST)
        if form.is_valid():
            file_link = form.cleaned_data['file_link']
            try:
                call_command('fetch_file_content', file_link)
                messages.success(request, 'Content has been successfully fetched from the file link.')
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
            return redirect('admin:thepopwinegdrives_book_changelist')
    else:
        form = FetchFileContentForm()
    context = dict(
        admin.site.each_context(request),
        form=form,
        title='Fetch File Content',
    )
    return render(request, 'admin/fetch_file_content_form.html', context)
