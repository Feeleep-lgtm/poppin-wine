from django.apps import AppConfig
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os

# Initialize the Slack App
slack_app = App(token=os.getenv("SLACK_BOT_TOKEN"))

class SlackbotConfig(AppConfig):
    name = 'slackbot'

    def ready(self):
        # Import actions to register them with slack_app
        import slackbot.actions  # Ensure actions are loaded
        print('actions imported in slackbot')
        # Start the Socket Mode client in a separate thread
        if os.getenv('RUN_MAIN') != 'true':  # Avoid starting twice with Django's autoreload
            handler = SocketModeHandler(slack_app, os.getenv("SLACK_APP_TOKEN"))
            handler.start_async()  # Use async to avoid blocking Django startup
