
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from kanban_app.api.utils import get_fullname

from .serializers import RegistrationSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            if not email or not password:
                return Response({'error': 'Invalid request data.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'Invalid request data.'}, status=status.HTTP_400_BAD_REQUEST)

            user = authenticate(
                request,
                username=user.username,
                password=password
            )

            if user is None:
                return Response({'error': 'Invalid request data.'}, status=status.HTTP_400_BAD_REQUEST)

            token, created = Token.objects.get_or_create(user=user)

            data = {
                'token': token.key,
                'fullname': get_fullname(user),
                'email': user.email,
                'user_id': user.id
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception:
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = RegistrationSerializer(data=request.data)

            data = {}

            if serializer.is_valid():
                saved_account = serializer.save()
                token, created = Token.objects.get_or_create(
                    user=saved_account)
                data = {
                    'token': token.key,
                    'fullname': saved_account.username,
                    'email': saved_account.email,
                    'user_id': saved_account.id
                }
                return Response(data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Invalid request data.'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
