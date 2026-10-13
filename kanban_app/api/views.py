from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from kanban_app.models import Boards, Tasks, Comments
from .serializers import BoardsSerializer, BoardViewSerializer, BoardUpdateSerializer, TasksSerializer, TasksViewSerializer, TaskUpdateSerializer, CommentsSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .permissions import IsBoardOwnerOrTaskCreator, IsBoardOwnerOrMember, IsCommentCreator, IsBoardOwner, IsBoardMember
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound, PermissionDenied
from django.core.validators import validate_email

class BoardsViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = BoardsSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'partial_update':
            permission_classes = [IsAuthenticated, IsBoardOwnerOrMember]

        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsBoardOwner]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'retrieve': #id des Boards
            return BoardViewSerializer

        return BoardsSerializer

    def get_queryset(self):
        user = self.request.user

        if self.action in ['partial_update', 'destroy']:
            return Boards.objects.all() #alle Boards finden

        return Boards.objects.filter(Q(owner=user) | Q(members=user)).distinct() #.distinct() Board kommt nur einmal zurück, siehe or Abfrage

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = BoardsSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = BoardUpdateSerializer(instance)
        return Response(response_serializer.data,status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = Boards.objects.filter(pk=kwargs.get('pk')).first()

        if instance is None: #Board existiert nicht
            raise NotFound('Board not found.')

        if instance.owner != request.user: #Nur der Board-Owner darf löschen
            raise PermissionDenied('The user must be the board owner to delete it.')
        
        self.check_object_permissions(request, instance)#Damit IsBoardOwner-Permission ausgeführt wird
        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)

class TasksViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = TasksSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'partial_update']:
            permission_classes = [IsAuthenticated, IsBoardMember]

        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsBoardOwnerOrTaskCreator]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TasksViewSerializer

        elif self.action == 'partial_update':
            return TaskUpdateSerializer

        return TasksSerializer

    def get_queryset(self):
        user = self.request.user

        if self.action in ['partial_update', 'destroy']:
            return Tasks.objects.all()

        return Tasks.objects.filter(Q(board__owner=user) | Q(board__members=user)).distinct()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)


    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        if 'board' in request.data:
            if str(request.data['board']) != str(instance.board_id):
                return Response({'error': 'Changing the board of a task is not allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data,status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(created_by=request.user)
        response_serializer = TasksViewSerializer(task)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = Tasks.objects.filter(pk=kwargs.get('pk')).first()

        if instance is None: #Task existiert nicht
            raise NotFound('Task not found.')

        if (instance.created_by != request.user and instance.board.owner != request.user):
            raise PermissionDenied('Only the task creator or board owner can delete this task.')
        
        self.check_object_permissions(request, instance)
        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)

class EmailCheck(APIView):
    permission_classes = [IsAuthenticated]

    # def post(self, request):
    def get(self, request): #Anforderung war get, nicht Post wie Login
        try:
            # email = request.data.get('email')
            email = request.query_params.get('email') #E-Mail aus Query-Parametern, Übergabe als Parameter in der Url

            if not email:
                return Response({'error': 'Email is required.'},status=status.HTTP_400_BAD_REQUEST)

            try:
                validate_email(email)

            except ValidationError:
                return Response({'error': 'Invalid email format.'},status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email__iexact=email) #iexact = case insensitive, exact = case sensitive

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

class MemberAssignedTasksView(generics.ListAPIView):
    serializer_class = TasksViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Tasks.objects.filter(Q(assignee=user) | Q(reviewer=user)).distinct()

class MemberReviewingTasksView(generics.ListAPIView):
    serializer_class = TasksViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Tasks.objects.filter(reviewer=user)

class CommentsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = CommentsSerializer
    permission_classes = [IsAuthenticated, IsCommentCreator]

    def get_queryset(self):
        task_id = self.kwargs.get('task_id')
        return Comments.objects.filter(task_id=task_id)

    def perform_create(self, serializer):
        task = Tasks.objects.get(pk=self.kwargs['task_id'])

        serializer.save(task=task,author=self.request.user)
