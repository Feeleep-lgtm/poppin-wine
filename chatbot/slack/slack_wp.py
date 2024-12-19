import requests
from django.conf import settings

def send_reply_to_wordpress(session_id, response):
    # Define your WordPress webhook URL
    webhook_url = 'https://poppinwinechatqa.local/wp-json/poppin-bot-chat/v1/chat-update'
    
    payload = {
        'session_id': session_id,
        'response': response,
    }
    
    # Send the POST request to WordPress
    response = requests.post(webhook_url, json=payload)
    
    if response.status_code != 200:
        print(f"Error sending data to WordPress: {response.content}")
