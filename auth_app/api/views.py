from rest_framework import generics
from .serializers import RegistrationSerializer #UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken

class LoginView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        data = {}
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            data = {
                'token': token.key,
                'fullname': user.username,
                'email': user.email,
                'user_id': user.id
            }
        else:
            data=serializer.errors

        return Response(data)

class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        data = {}
        if serializer.is_valid():
            saved_account = serializer.save()
            token, created = Token.objects.get_or_create(user=saved_account) #könnte schon vorhanden sein, braucht created wegen Tupel
            data = {
                'token': token.key,
                'username': saved_account.username,
                'email': saved_account.email
            }
        else:
            data=serializer.errors

        return Response(data)
