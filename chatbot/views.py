from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import auth
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .models import Chat, UserPreferences, ClientApp, APIChat, AnonymousChat, ChatSession
from thepopwinegdrives.models import Book, ScrapedContent

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, generics

from rest_framework_simplejwt.views import TokenObtainPairView
from .utils import ask_openai, query_chroma_db 
from .authentication import CustomJWTAuthentication, APIKeyAuthentication, get_anonymous_token
from thepopwinegdrives.serializers import CustomTokenObtainPairSerializer 
import os
import requests 
from slackbot.slack_utils import talk_to_slack, post_ai_response_to_slack,send_approval_message_to_slack, get_ai_response  # Import from slackbot

import logging
import traceback

logger = logging.getLogger(__name__)
random_channel = 'C14P7K62Z' # random channel id

 
# Standard chatbot view for authenticated users
@login_required
def chatbot(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == 'POST':
        message = request.POST.get('message')
        response = query_chroma_db(message)
        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
        chat.save()
        return JsonResponse({'message': message, 'response': response})

    books = Book.objects.all()
    scraped_contents = ScrapedContent.objects.all()
    user_preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
    selected_books = user_preferences.selected_books.values_list('id', flat=True)
    selected_scraped_contents = user_preferences.selected_scraped_contents.values_list('id', flat=True)

    return render(request, 'chatbot.html', {
        'chats': chats,
        'books': books,
        'scraped_contents': scraped_contents,
        'selected_books': selected_books,
        'selected_scraped_contents': selected_scraped_contents,
    })

 
def extract_chat_id_from_message(thread_ts):
    # Assuming `thread_ts` is stored as metadata in the initial Slack message (modify as needed)
    # This function needs to be implemented based on how `chat_id` is embedded or stored in Slack
    try:
        chat_id = int(thread_ts.split('.')[0])  # Example if `thread_ts` contains the chat ID
        return chat_id
    except ValueError:
        return None
    


class UserChatsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        chats = Chat.objects.filter(user_id=user_id)
        serialized_chats = [
            {
                "user": chat.user.username,
                "message": chat.message,
                "response": chat.response,
                "created_at": chat.created_at
            }
            for chat in chats
        ]
        return Response(serialized_chats, status=200)
    



class AnonymousChatCreateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        print(' requests ', request)
        try:
            logger.info("Received POST request in AnonymousChatCreateView")
            message = request.data.get('message')
            session_id = request.data.get('session_id')
            admin_available = request.data.get('admin_available', False)
            query_type = request.data.get('query_type', 'chroma')
            logger.info(f"Message: {message}, Session ID: {session_id}, Admin Available: {admin_available}, Query Type: {query_type}")

            print(' message ', message)
            # Validate inputs
            if not session_id or not message:
                logger.error("Session ID or message is missing.")
                return Response({"error": "Session ID and message are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Get or create ChatSession
            session, _ = ChatSession.objects.get_or_create(session_id=session_id)
            thread_ts = session.slack_thread_ts

            # Send message to Slack if admin is available
            slack_response = None
            if admin_available:
                slack_response = talk_to_slack(message, thread_ts=thread_ts)
                logger.info(f"Slack response: {slack_response}")

                if not thread_ts:
                    session.slack_thread_ts = slack_response['ts']
                    session.save()

            # Save the user message in AnonymousChat
            chat = AnonymousChat.objects.create(
                session=session,
                message=message,
                created_at=timezone.now(),
                is_admin_response=False,  # Mark as user message
                slack_message_ts=slack_response.get('ts') if slack_response else None,  
                slack_thread_ts=slack_response.get('thread_ts', slack_response['ts']) if slack_response else None
            )
            logger.info(f"chat saved response: {chat}")


            # Process the response (OpenAI or Chroma)
            try:
                response_text = get_ai_response(message, query_type)
                if not response_text:
                    raise ValueError("AI response was empty or None")
            except Exception as ai_error:
                logger.error(f"Error retrieving AI response: {ai_error}")
                response_text = "There was an error processing the AI response. Please review manually."
                send_approval_message_to_slack(response_text, session.slack_thread_ts)
                return Response({
                    'message': message,
                    'message_timestamp': chat.created_at,
                    'response': response_text,
                    'response_timestamp': timezone.now(),
                }, status=status.HTTP_200_OK) 
            print(' ai response_text ', response_text)
            # Post AI response to a dedicated Slack channel for admin review
            send_approval_message_to_slack(response_text, session.slack_thread_ts) 
            # post_ai_response_to_slack(response_text, session.slack_thread_ts) 
            # Return response with timestamps and generated response text
            return Response({
                'message': message,
                'message_timestamp': chat.created_at,
                'response': response_text,
                'response_timestamp': timezone.now(),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Error in AnonymousChatCreateView")
            return Response({"error": "An error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# class AnonymousChatCreateView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         try:
#             message_received_time = timezone.now()
#             session_id = request.data.get('session_id')
#             message = request.data.get('message')
#             admin_available = request.data.get('admin_available', False)
#             query_type = request.data.get('query_type', 'chroma')

#             # Validate session ID and message
#             if not session_id:
#                 return Response({"error": "Session ID is required"}, status=status.HTTP_400_BAD_REQUEST)

#             if not message:
#                 return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

#             # Create or get the ChatSession by session_id
#             session, created = ChatSession.objects.get_or_create(session_id=session_id)
#             thread_ts = session.slack_thread_ts  # Use thread_ts for replies, otherwise, None for new threads

#             # Send message to Slack if admin is available
#             if admin_available:
#                 post_msg_response = talk_to_slack(message, thread_ts=thread_ts)

#                 # For new sessions or first message, save the returned ts as the thread_ts
#                 if created or not session.slack_thread_ts:
#                     session.slack_thread_ts = post_msg_response['ts']  # Save ts for the first message in the thread
#                     session.save()

#             # Process the response (OpenAI or Chroma)
#             if query_type == "openai":
#                 response_text = ask_openai(message)
#             else:
#                 response_text = query_chroma_db(message)

#             # Save the chat in the AnonymousChat model
#             # Use `thread_ts` if available; if not, use `ts`
#             print(f" we get thread_ts from post_msg_response.get('thread_ts') {post_msg_response.get('thread_ts')}")
#             chat = AnonymousChat.objects.create(
#                 session=session,
#                 message=message,
#                 response=response_text,
#                 created_at=message_received_time,
#                 slack_message_ts=post_msg_response.get('ts'),  # Store the ts of this message (for replies or standalone)
#                 slack_thread_ts=post_msg_response.get('thread_ts', post_msg_response['ts'])  # Use thread_ts or fallback to ts
#             )

#             # Return the response with the created chat details
#             return Response({
#                 'message': message,
#                 'message_timestamp': chat.created_at,
#                 'response': response_text,
#                 'response_timestamp': timezone.now(),
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.exception("An error occurred while handling the request.")
#             print("An error occurred:", str(e))
#             traceback.print_exc()  # This will print the full traceback of the error 
#             return Response({"error": "Something went wrong on the server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# API view for handling chat submissions via API
class APIChatCreateView(APIView):
    authentication_classes = [CustomJWTAuthentication, APIKeyAuthentication]
    permission_classes = [AllowAny]
    
    def post(self, request):
        message_received_time = timezone.now()
        client_id = request.data.get('client_id')
        print('new api chat request...message: ', request.data.get('message'))
        if not client_id:
            return Response({"error": "Client ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate client_id by checking it against the ClientApp model
        try:
            client_app = ClientApp.objects.get(client_id=client_id)
        except ClientApp.DoesNotExist:
            return Response({"error": "Invalid Client ID"}, status=status.HTTP_400_BAD_REQUEST)

        message = request.data.get('message')
        if not message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user wants to query Chroma or OpenAI
        query_type = request.data.get('query_type', 'chroma')  # Default is Chroma

        if query_type == 'chroma':
            response_text = query_chroma_db(message)
        elif query_type == 'openai':
            # context = request.data.get('context', '')  # You can pass additional context if needed
            response_text = ask_openai(message)
        else:
            return Response({"error": "Invalid query type"}, status=status.HTTP_400_BAD_REQUEST)
   
        # Save the chat in the APIChat model
        api_chat = APIChat.objects.create(
            client_id=client_app,
            message=message,
            response=response_text,
            created_at=message_received_time
        )
        api_chat.save()

        return Response({
            'message': message,
            'message_timestamp': api_chat.created_at,  # Timestamp of the message
            'response': response_text,
            'response_timestamp': timezone.now()  # Timestamp of the response 
        }, status=status.HTTP_200_OK)

# API view for retrieving chats associated with a specific client app
class ClientAppChatsAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, client_app_id):
        chats = APIChat.objects.filter(client_id=client_app_id)
        serialized_chats = [
            {"client_id": chat.client_id.client_id, "message": chat.message, "response": chat.response, "created_at": chat.created_at}
            for chat in chats
        ]
        return Response(serialized_chats, status=status.HTTP_200_OK)

# API view for generating an anonymous JWT token
class AnonymousTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        client_id = request.data.get('client_id')
        if not client_id:
            return Response({"error": "Client ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        tokens = get_anonymous_token(client_id)
        return Response(tokens, status=status.HTTP_200_OK)

class AnonymousChatsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        chats = Chat.objects.filter(user__isnull=True)
        serialized_chats = [
            {
                "client_app_id": chat.client_app_id,
                "message": chat.message,
                "response": chat.response,
                "created_at": chat.created_at
            }
            for chat in chats
        ]
        return Response(serialized_chats, status=200)
# Custom Token Obtain Pair View to add client_id claim during login (if needed)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Standard login view
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')

# Standard register view
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = 'Error creating account'
                return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = 'Passwords don\'t match'
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

# Standard logout view
def logout(request):
    auth.logout(request)
    return redirect('login')
