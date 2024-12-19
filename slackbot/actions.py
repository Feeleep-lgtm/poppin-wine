from .apps import slack_app
import logging 

logger = logging.getLogger(__name__)


@slack_app.action("approve")
def handle_approve(ack, body, client):
    logger.info("firing slack_app.action approve from Slack")
    ack()  # Acknowledge the action
    channel_id = body['channel']['id']
    message_ts = body['message']['ts']
    user = body['user']['id']
    
    client.chat_postMessage(
        channel=channel_id,
        text=f"Response approved by <@{user}> and posted.",
        thread_ts=message_ts
    )

@slack_app.action("edit")
def handle_edit(ack, body, client):
    logger.info("firing slack_app.action edit from Slack")
    ack()  # Acknowledge the action
    channel_id = body['channel']['id']
    message_ts = body['message']['ts']
    
    client.chat_postMessage(
        channel=channel_id,
        text="You can edit the response here and then click 'Post' when ready.",
        thread_ts=message_ts
    )

@slack_app.action("post")
def handle_post(ack, body, client):
    logger.info("firing slack_app.action post from Slack")
    ack()  # Acknowledge the action
    channel_id = body['channel']['id']
    message_ts = body['message']['ts']
    
    client.chat_postMessage(
        channel=channel_id,
        text="The response has been posted as finalized.",
        thread_ts=message_ts
    )

@slack_app.action("cancel")
def handle_cancel(ack, body, client):
    logger.info("firing slack_app.action cancel from Slack")
    ack()  # Acknowledge the action
    channel_id = body['channel']['id']
    message_ts = body['message']['ts']
    user = body['user']['id']
    
    client.chat_postMessage(
        channel=channel_id,
        text=f"The approval process was canceled by <@{user}>.",
        thread_ts=message_ts
    )
