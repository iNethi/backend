"""
Views for the user API
"""
from django.contrib.auth import get_user_model
from keycloak.exceptions import (
    KeycloakAuthenticationError,
    KeycloakConnectionError,
    KeycloakError
)
from rest_framework import serializers
from rest_framework import generics, permissions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import ValidationError

from rest_framework.response import Response
from rest_framework.settings import api_settings

from django.conf import settings
from rest_framework.views import APIView

from utils.keycloak import KeycloakAuthentication
from .serializers import (
    UserSerializer,
    KeycloakAuthTokenSerializer
)


def create_user(**params):
    """Helper function to create a user"""
    return get_user_model().objects.create_user(**params)


def update_keycloak_user(user, data):
    """Helper method to update the user in Keycloak"""
    try:
        # Retrieve the Keycloak user ID based on the Django user
        keycloak_user_id = settings.KEYCLOAK_ADMIN.get_user_id(user.username)
        # Prepare the Keycloak update payload
        keycloak_payload = {
            "firstName": data.get("first_name", user.first_name),
            "lastName": data.get("last_name", user.last_name),
            "email": user.email,
            "username": user.username,
            "enabled": user.is_active,
        }

        # Update the Keycloak user
        settings.KEYCLOAK_ADMIN.update_user(keycloak_user_id, keycloak_payload)

    except KeycloakAuthenticationError:
        raise ValidationError(
            {'detail': 'Authentication with Keycloak failed.'}, code=401
        )

    except KeycloakConnectionError:
        raise ValidationError(
            {'detail': 'Unable to connect to Keycloak server.'}, code=503
        )

    except KeycloakError as e:
        raise ValidationError(
            {'detail': f'Keycloak error: {str(e)}'}, code=400
        )


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for the user"""
    serializer_class = KeycloakAuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        # Use the KeycloakAuthTokenSerializer
        serializer = self.serializer_class(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            print(serializer.errors)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        keycloak_token = serializer.validated_data.get('token')
        refresh_token = serializer.validated_data.get('refresh_token')
        expires_in = serializer.validated_data.get('expires_in')
        # Return response based on the type of authentication
        return Response({
            'token': keycloak_token,
            'refresh_token': refresh_token,
            'expires_in': expires_in
        }, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """View to refresh the access token"""
    serializer = KeycloakAuthTokenSerializer()

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'Refresh token required.'}, status=400)

        try:
            token_data = self.serializer.refresh_token_if_needed(refresh_token)
            return Response(token_data, status=200)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user"""
    serializer_class = UserSerializer
    authentication_classes = (KeycloakAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        """Retrieve the authenticated user"""
        return self.request.user

    def update(self, request, *args, **kwargs):
        """Override the update method to sync updates with Keycloak"""
        user = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)

        # Save the changes to the Django user
        self.perform_update(serializer)

        # Update Keycloak with the new details
        update_keycloak_user(user, request.data)

        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """Override the patch method"""
        return self.update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """Override the put method"""
        return self.update(request, *args, **kwargs)
