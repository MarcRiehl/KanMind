from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from kanban_app.models import Boards, Tasks, Comments
from .serializers import BoardsSerializer, BoardViewSerializer, BoardUpdateSerializer, TasksSerializer, TasksViewSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .permissions import IsBoardOwnerOrTaskCreator, IsBoardOwnerOrMember
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

class BoardsViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = BoardsSerializer
    permission_classes = [IsAuthenticated]


    def get_serializer_class(self):
        if self.action == 'retrieve': #id des Boards
            return BoardViewSerializer

        return BoardsSerializer

    def get_queryset(self):
        user = self.request.user

        return Boards.objects.filter(Q(owner=user) | Q(members=user)).distinct() #.distinct() Board kommt nur einmal zurück, siehe or Abfrage

    def get_permissions(self):
        permission_classes = [IsAuthenticated]

        if self.action == 'partial_update':
            permission_classes = [IsBoardOwnerOrMember]

        return [permission() for permission in permission_classes]

    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = BoardsSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = BoardUpdateSerializer(instance)
        return Response(response_serializer.data,status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class MemberAssignedTasks(generics.ListCreateAPIView):
    pass

class MemberReviewing(generics.ListCreateAPIView):
    pass

class TasksViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = TasksSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return TasksViewSerializer
        elif self.action == 'retrieve':
            return TasksViewSerializer
        return TasksSerializer

    def get_queryset(self):
        user = self.request.user

        return Tasks.objects.filter(Q(board__owner=user) | Q(board__members=user)).distinct()

    # def perform_create(self, serializer):
    #     serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(created_by=request.user)
        response_serializer = TasksViewSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsBoardOwnerOrTaskCreator]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]


class CommentsViewSet(viewsets.ModelViewSet):
    pass


class EmailCheck(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            email = request.data.get('email')

            if not email:
                return Response({'error': 'Email is required.'},status=status.HTTP_400_BAD_REQUEST)

            try:
                validate_email(email)

            except ValidationError:
                return Response({'error': 'Invalid email format.'},status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email__iexact=email) #iexact = case insensitive
                
            except User.DoesNotExist:
                return Response({'error': 'Email not found.'}, status=status.HTTP_404_NOT_FOUND)

            data = {
                'user_id': user.id,
                'email': user.email,
                'fullname': user.username
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception:
            return Response({'error': 'Internal server error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
