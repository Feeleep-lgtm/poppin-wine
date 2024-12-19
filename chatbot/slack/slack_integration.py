import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from ..models import AnonymousChat
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
import os 
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

SLACK_TOKEN = os.getenv('SLACK_TOKEN', 'slack-bot-token') 
app = App(token=SLACK_TOKEN)
random_channel = 'C14P7K62Z' # random channel id

# Load environment variables from .env file
# load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env.production')
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env.development')
@csrf_exempt
def slack_events(request):
    """
    Handles Slack Events API requests sent to the Django server.
    Processes Slack's verification challenge and event messages.
    """
    if request.method == 'POST':
        event_data = json.loads(request.body)

        # Respond to Slack URL verification challenge
        if 'challenge' in event_data:
            return JsonResponse({'challenge': event_data['challenge']})

        # Handle the actual Slack event (message, admin reply, etc.)
        if 'event' in event_data:
            event = event_data['event']

            # Handling Slack message events (e.g., user messages or admin replies)
            if event.get('type') == 'message':
                user_message = event.get('text', '')
                slack_user_id = event.get('user')  # Slack user who sent the message
                channel_id = event.get('channel')
                thread_ts = event.get('thread_ts', None)  # If it's part of a thread

                if 'thread_ts' in event:
                    # Admin reply handling (when it's part of a thread)
                    handle_slack_reply(event)
                else:
                    # New message from a user
                    session_id = event.get('ts')  # Use the message ts as a session_id
                    handle_incoming_message(session_id, user_message, slack_user_id, channel_id)

        return JsonResponse({'status': 'ok'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)



def handle_incoming_message(session_id, message, slack_user_id, channel_id):
    """
    Handles incoming messages from users and sends them to Slack.
    """
    # Save the chat in the database
    message_received_time = timezone.now()

    chat = AnonymousChat.objects.create(
        session_id=session_id,
        message=message,
        slack_user_id=slack_user_id,
        created_at=message_received_time
    )
    chat.save()

    # Forward the message to Slack for admin attention
    send_message_to_slack(session_id, message, channel_id)

 
def handle_slack_reply(event):
    """
    Handles admin replies from Slack and updates the corresponding chat in the database.
    """
    thread_ts = event['thread_ts']  # Session ID (used as thread_ts)
    admin_message = event['text']  # Admin's response

    try:
        # Find the matching chat based on session_id (thread_ts)
        chat = AnonymousChat.objects.get(session_id=thread_ts)
        chat.response = admin_message  # Update the response with admin's message
        chat.response_timestamp = timezone.now()
        chat.save()

        # Push the updated response to WordPress via webhook
        webhook_url = 'https://poppinwineclub.com/wp-json/your-plugin/v1/chat-update'
        data = {
            'session_id': thread_ts,
            'response': admin_message,
            'response_timestamp': str(chat.response_timestamp),
        }
        requests.post(webhook_url, json=data)

    except AnonymousChat.DoesNotExist:
        print(f"Chat with Session ID {thread_ts} not found.")


def send_message_to_slack(session_id, message, channel_id):
    """
    Sends the user's message to a Slack channel to notify admins.
    """
    slack_webhook_url = 'https://hooks.slack.com/services/your/slack/webhook'
    headers = {'Content-Type': 'application/json'}

    slack_message = {
        "channel": channel_id,  # Send the message to the same Slack channel
        "text": f"New message from user (Session ID: {session_id})\nMessage: {message}\nPlease reply in this thread.",
        "thread_ts": session_id  # Start a thread for this conversation
    }

    response = requests.post(slack_webhook_url, headers=headers, json=slack_message)
    if response.status_code != 200:
        raise Exception(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")

 
def talk_to_slack(message, thread_ts=None):
    client = WebClient(token=SLACK_TOKEN)
    try:
        response = client.chat_postMessage(
            channel='#random',  # Replace with the correct channel
            text=message,
            thread_ts=thread_ts  # Use the thread_ts if it’s a reply, otherwise start a new thread
        )

        return response  # Contains 'ts' and possibly 'thread_ts'
    except SlackApiError as e:
        print(f"Error sending message to Slack: {e.response['error']}")
        raise e

def get_conversation_history(channel):
    channel_id='C14P7K62Z' #random channel
    client = WebClient(token=SLACK_TOKEN)
    response = client.conversations_history(channel=channel_id )
    return response

# get threads  
def get_conversation_replies(channel, thread):
    channel_id=channel # random_channel 
    client = WebClient(token=SLACK_TOKEN)
    response = client.conversations_replies(channel=channel_id, inclusive=True, ts=thread )
    return response 

 
