# slackbot/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from chatbot.models import AnonymousChat, ChatSession
from .slack_utils import talk_to_slack
import logging
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
import requests
import os

logger = logging.getLogger(__name__)

SLACK_TOKEN=os.getenv('SLACK_TOKEN')
SLACK_CLIENT_ID = os.getenv('SLACK_CLIENT_ID')
SLACK_CLIENT_SECRET= os.getenv('SLACK_CLIENT_SECRET')
SLACK_REDIRECT_URI= 'https://5bb2-2603-8000-1b00-2730-1412-a9e6-c7fe-b87.ngrok-free.app/slack/oauth_redirect' # os.getenv('SLACK_TOKEN')
client = WebClient(token=SLACK_TOKEN)

def slack_oauth_redirect(request):
    # Get the `code` parameter from Slack's response
    code = request.GET.get('code')
    if not code:
        return HttpResponse("No code provided", status=400)

    # Exchange the code for an access token
    response = requests.post(
        'https://slack.com/api/oauth.v2.access',
        data={
            'client_id': SLACK_CLIENT_ID,
            'client_secret': SLACK_CLIENT_SECRET,
            'code': code,
            'redirect_uri': SLACK_REDIRECT_URI,  # Same as in Slack App settings
        }
    )
    data = response.json()
    if not data.get("ok"):
        return JsonResponse({"error": data.get("error")}, status=400)

    # Process the data and store tokens as needed
    # You may redirect to a success page or return a message
    return HttpResponse("Slack OAuth flow completed successfully!")
# @csrf_exempt
# def slack_events(request):
#     """
#     Endpoint to handle Slack events.
#     """
#     if request.method == 'POST':
#         event_data = json.loads(request.body)

#         # Respond to Slack verification challenge
#         if 'challenge' in event_data:
#             return JsonResponse({'challenge': event_data['challenge']})

#         # Process Slack events
#         if 'event' in event_data:
#             event = event_data['event']
#             if event.get('type') == 'message' and "bot_id" not in event:
#                 handle_slack_message(event)

#         return JsonResponse({'status': 'ok'}, status=200)

#     return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
@csrf_exempt
def slack_interaction(request):
    if request.method == "POST":
        payload = json.loads(request.POST.get("payload"))
        action_id = payload.get("actions")[0].get("action_id")
        response_url = payload.get("response_url")

        if action_id == "approve":
            # Handle approval logic here
            client.chat_postMessage(channel=payload["channel"]["id"], text="Response approved!")
        elif action_id == "reject":
            # Handle rejection logic here
            client.chat_postMessage(channel=payload["channel"]["id"], text="Response rejected!")
        else:
            # Fallback message
            client.chat_postMessage(channel=payload["channel"]["id"], text="Unknown action.")
        
        return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)



@csrf_exempt
def slack_events(request):
    if request.method == 'POST':
        event_data = json.loads(request.body)

        # Respond to Slack verification challenge
        if 'challenge' in event_data:
            return JsonResponse({'challenge': event_data['challenge']})

        # Process Slack events
        if 'event' in event_data:
            event = event_data['event']
            if event.get('type') == 'message' and "bot_id" not in event:
                process_admin_response(event)

        return JsonResponse({'status': 'ok'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


def process_admin_response(event):
    """
    Processes an admin's response to a user message, associating it with the correct session and message.
    """
    slack_ts = event.get('ts')
    thread_ts = event.get('thread_ts')
    admin_message = event.get('text')
    print('admin message received...', admin_message)
    # Find the ChatSession by thread_ts
    try:
        session = ChatSession.objects.get(session_id=thread_ts)
        
        # Save the admin response in AnonymousChat
        AnonymousChat.objects.create(
            session=session,
            message=admin_message,
            is_admin_response=True,
            slack_message_ts=slack_ts,
            slack_thread_ts=thread_ts,
            created_at=timezone.now()
        )
        logger.info(f"Admin response saved for session: {session.session_id}")

    except ChatSession.DoesNotExist:
        logger.error(f"No session found for thread_ts {thread_ts}")



def handle_slack_message(event):
    """
    Handles incoming Slack messages, storing admin responses and linking them to sessions.
    """
    slack_user_id = event.get('user')
    message = event.get('text')
    slack_ts = event.get('ts')
    thread_ts = event.get('thread_ts') or slack_ts

    # Link message to session or create new session
    session, created = ChatSession.objects.get_or_create(session_id=thread_ts)
    AnonymousChat.objects.create(
        session=session,
        message=message,
        created_at=timezone.now(),
        slack_message_ts=slack_ts,
        slack_thread_ts=thread_ts,
        is_admin_response=True  # Mark as admin response
    )
    logger.info(f"Stored Slack admin message for session {session.session_id}")
