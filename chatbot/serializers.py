# chatbot/serializers.py 
from rest_framework import serializers
from .models import Chat, APIChat, AnonymousChat, ChatSession  # Correctly import the Chat model

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat  # Reference the correct model
        fields = ['id', 'user', 'message', 'response', 'created_at']  # Fields to be serialized
        read_only_fields = ['response', 'created_at']  # Fields that shouldn't be modified

class APIChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIChat
        fields = '__all__'

    def validate_client_id(self, value):
        if not value:
            raise serializers.ValidationError("Client ID is required for API chats.")
        return value
    

class AnonymousChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnonymousChat
        fields = ['session_id', 'message', 'response', 'created_at']
        read_only_fields = ['response', 'created_at']

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['session_id', 'created_at']  # You can add more fields as needed
        read_only_fields = ['created_at']