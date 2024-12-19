# slackbot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.slack_events, name='slack_events'),
    path('oauth_redirect/', views.slack_oauth_redirect, name='slack_oauth_redirect'),

]
