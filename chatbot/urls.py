# chatbot/urls.py
from django.urls import path
from .views import (
    chatbot,
    ClientAppChatsAPIView,
    UserChatsAPIView,
    AnonymousChatsAPIView,
    AnonymousChatCreateView,
    AnonymousTokenView,
    APIChatCreateView,
    login,
    register,
    logout
)
from .slack.slack_integration  import slack_events
urlpatterns = [
    path('', chatbot, name='chatbot'),  # Main chatbot view for authenticated users
    path('api/token/anonymous/', AnonymousTokenView.as_view(), name='token_anonymous'),  # API for generating anonymous tokens
    path('api/chat/', APIChatCreateView.as_view(), name='api-chat-create'),  # API endpoint for creating chat records via API
    path('api/chats/client/<str:client_app_id>/', ClientAppChatsAPIView.as_view(), name='client_app_chats'),  # API for retrieving chats by client_app_id
    path('api/chats/user/<int:user_id>/', UserChatsAPIView.as_view(), name='user_chats'),  # API for retrieving chats by user_id
    path('api/chats/anonymous/', AnonymousChatsAPIView.as_view(), name='anonymous_chats'),  # API for retrieving anonymous chats
    path('api/chats/c/anonymous/', AnonymousChatCreateView.as_view(), name='anonymous-chat-create'),  # API for retrieving anonymous chats
    # path('slack/events/', slack_events, name='slack_events'),

    path('login', login, name='login'),  # User login view
    path('register', register, name='register'),  # User registration view
    path('logout', logout, name='logout'),  # User logout view
]
