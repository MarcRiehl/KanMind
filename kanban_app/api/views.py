from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from kanban_app.models import Boards, Tasks, Comments
from .serializers import BoardsSerializer

class BoardsView(generics.ListCreateAPIView):
    queryset = Boards.objects.all()
    serializer_class = BoardsSerializer