from django.db import models
import uuid
# Create your models here.

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    last_accessed = models.DateTimeField()  # Changed to DateTimeField
    content = models.TextField(null=True, blank=True)  # Add content field

    def __str__(self):
        return self.title

class ScrapedContent(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Script(models.Model):
    name = models.CharField(max_length=100)
    task_name = models.CharField(max_length=100, blank=True, null=True)
    is_running = models.BooleanField(default=False)
    last_run = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class ClientApp(models.Model):
# Immutable and unique client ID
    client_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) 
    name = models.CharField(max_length=255, unique=True) 
    api_key = models.CharField(max_length=255, unique=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.client_id})"
    