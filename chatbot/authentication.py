from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from thepopwinegdrives.models import ClientApp

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('Authorization')
        if not api_key:
            raise AuthenticationFailed('API key required')

        try:
            client_app = ClientApp.objects.get(api_key=api_key)
        except ClientApp.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')

        return (client_app, None)  # Return the client app instead of (None, None)
 
class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        validated_token = super().authenticate(request)
        if validated_token is None:
            return None

        user, token = validated_token

        # Validate client_id claim, but only if it's supposed to be there
        client_id = token.get('client_id')
        if client_id:
            client_app = ClientApp.objects.filter(client_id=client_id).first()
            if not client_app:
                raise AuthenticationFailed('Invalid client ID')
            request.auth = client_app  # Attach the client app to the request

        return user, token

# This is for logged-in users who need a JWT token with a client_id
def get_user_token_with_client_id(user, client_id):
    refresh = RefreshToken.for_user(user)
    refresh['client_id'] = client_id
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

 # Function to generate a token with client_id for anonymous users or client app interactions
def get_anonymous_token(client_id):
    refresh = RefreshToken()
    refresh['client_id'] = client_id
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
