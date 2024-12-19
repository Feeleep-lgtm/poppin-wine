#serializers.py
from rest_framework import serializers
from .models import Book, ScrapedContent
from .models import ClientApp
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['title', 'author', 'last_accessed', 'content']

class ScrapedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapedContent
        fields = ['url', 'title', 'content', 'created_at']


class ClientAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientApp
        fields = ['name', 'api_key']
    
    def validate_name(self, value):
        if self.instance:  # if updating
            if ClientApp.objects.filter(name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A client app with this name already exists.")
        else:  # if creating
            if ClientApp.objects.filter(name=value).exists():
                raise serializers.ValidationError("A client app with this name already exists.")
        return value
    


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # client_app = ClientApp.objects.get(user=self.user)
        # client_id = client_app.client_id
        # refresh = self.get_token(self.user)
        # refresh['client_id'] = client_id
        # data['client_id'] = client_id
        return data