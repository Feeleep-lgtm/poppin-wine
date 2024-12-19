# chatbot/models
from django.db import models
from django.contrib.auth.models import User
from thepopwinegdrives.models import ClientApp, Book, ScrapedContent
from django.utils import timezone
class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat on {self.created_at} by {self.user.username if self.user else 'Anonymous'}"

class APIChat(Chat):
    client_id = models.ForeignKey(ClientApp, to_field='client_id', on_delete=models.CASCADE)

    def __str__(self):
        return f"API Chat on {self.created_at} via {self.client_id.name}"

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    selected_books = models.ManyToManyField(Book)
    selected_scraped_contents = models.ManyToManyField(ScrapedContent)

# New AnonymousChat model
class ChatSession(models.Model):
    session_id = models.CharField(max_length=255, unique=True)  # The session ID, could be the same as the Slack thread_ts
    slack_thread_ts = models.CharField(max_length=255, null=True, blank=True)  # The thread_ts for Slack conversation thread
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id}"


class AnonymousChat(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='chats')
    message = models.TextField()  # User's message
    response = models.TextField(null=True, blank=True)  # Admin's response or automated response
    created_at = models.DateTimeField(default=timezone.now)
    response_timestamp = models.DateTimeField(null=True, blank=True)  # Admin response time
    is_admin_response = models.BooleanField(default=False)  # New field to track if message is from admin

    # Slack-related fields
    slack_message_ts = models.CharField(max_length=50, null=True, blank=True)  # The individual message's `ts`
    slack_thread_ts = models.CharField(max_length=50, null=True, blank=True)  # The thread timestamp

    def __str__(self):
        return f"Chat in Session {self.session.session_id} at {self.created_at}"