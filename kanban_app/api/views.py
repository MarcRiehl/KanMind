from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from kanban_app.models import Boards, Tasks, Comments
from .serializers import BoardsSerializer, TasksSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

class BoardsViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = BoardsSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        user = self.request.user

        return Boards.objects.filter(Q(owner=user) | Q(members=user)).distinct() #.distinct() Board kommt nur einmal zurück, siehe or Abfrage

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class EmailCheck(APIView):
    pass

class MemberAssignedTasks(generics.ListCreateAPIView):
    pass

class MemberReviewing(generics.ListCreateAPIView):
    pass

class TasksViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = TasksSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Tasks.objects.filter(Q(board__owner=user) | Q(board__members=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    #musss noch eine eine eigene permission geschrieben werden

class CommentsViewSet(viewsets.ModelViewSet):
    pass