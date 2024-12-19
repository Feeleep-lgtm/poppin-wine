import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
from chatbot.utils import ask_openai, query_chroma_db  # Assuming these are defined elsewhere

# Initialize Slack client
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
client = WebClient(token=SLACK_TOKEN)
logger = logging.getLogger(__name__)

def get_ai_response(message, query_type):
    """
    Generates an AI response based on the specified query type.
    """
    if query_type == "openai":
        return ask_openai(message)
    return query_chroma_db(message)




def talk_to_slack(message, thread_ts=None, channel='#random'):
    """
    Send a message to Slack, either as a new thread or as a reply in an existing thread.
    """
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=message,
            thread_ts=thread_ts  # Post in thread if thread_ts is provided
        )
        return response  # Returns Slack's message timestamp and thread_ts
    except SlackApiError as e:
        logger.error(f"Error sending message to Slack: {e.response['error']}")
        raise e



def get_conversation_history(channel_id):
    """
    Retrieve conversation history for a specific Slack channel.
    """
    try:
        response = client.conversations_history(channel=channel_id)
        return response
    except SlackApiError as e:
        logger.error(f"Error retrieving conversation history: {e.response['error']}")
        raise e




def get_conversation_replies(channel_id, thread_ts):
    """
    Retrieve replies in a specific Slack thread.
    """
    try:
        response = client.conversations_replies(channel=channel_id, ts=thread_ts)
        return response
    except SlackApiError as e:
        logger.error(f"Error retrieving conversation replies: {e.response['error']}")
        raise e



def post_ai_response_to_slack(response_text, thread_ts, review_channel='#random'):
    """
    Posts the AI-generated response to a Slack channel for admin review.
    """
    try:
        response = client.chat_postMessage(
            channel=review_channel,
            text=f"AI response generated for review:\n\n{response_text}",
            thread_ts=thread_ts  # Post in the thread of the original message
        )
        return response
    except SlackApiError as e:
        logger.error(f"Error posting AI response to Slack: {e.response['error']}")
        raise e
    


def send_approval_message_to_slack(response_text, thread_ts, review_channel='#random'):
    # Define the message blocks with additional options
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Please review this AI-generated response:\n\n{response_text}"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Approve"
                    },
                    "action_id": "approve"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Edit"
                    },
                    "action_id": "edit"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Post"
                    },
                    "action_id": "post"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Cancel"
                    },
                    "action_id": "cancel"
                }
            ]
        }
    ]
    
    try:
        # Send the message to Slack with the action buttons
        response = client.chat_postMessage(
            channel=review_channel,
            text="Please review and approve the generated AI response.",  # Fallback text for accessibility
            thread_ts=thread_ts,  # Post in the thread of the original message
            blocks=blocks  # Pass blocks as a list of dictionaries
        )
        return response
    except SlackApiError as e:
        logger.error(f"Error posting AI response to Slack: {e.response['error']}")
        raise e
    