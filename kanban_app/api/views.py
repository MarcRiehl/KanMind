from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count, Q
from rest_framework import generics, mixins, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kanban_app.models import Boards, Comments, Tasks

from .permissions import (IsBoardMember, IsBoardOwner, IsBoardOwnerOrMember,
                          IsBoardOwnerOrTaskCreator, IsCommentCreator)
from .serializers import (BoardsSerializer, BoardUpdateSerializer,
                          BoardViewSerializer, CommentsSerializer,
                          TasksSerializer, TasksViewSerializer,
                          TaskUpdateSerializer)
from .utils import get_fullname


class BoardsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing boards with appropriate permissions and serializers."""
    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = BoardsSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.

        Returns:
            List of permission instances required for the current action.
        """
        if self.action == 'partial_update':
            permission_classes = [IsAuthenticated, IsBoardOwnerOrMember]

        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsBoardOwner]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return the serializer class for the current action.

        Returns:
            Serializer class corresponding to the current action.
        """
        if self.action == 'retrieve':
            return BoardViewSerializer

        return BoardsSerializer

    def get_queryset(self):
        """
        Return the queryset of boards based on the current user's permissions and action.

        Returns:
            QuerySet: Boards accessible to the current user.
        """
        user = self.request.user

        if self.action in ['partial_update', 'destroy']:
            return Boards.objects.all()

        queryset = Boards.objects.filter(
            Q(owner=user) |
            Q(pk__in=Boards.objects.filter(members=user).values('pk'))
        )

        return boards_with_counts(queryset)

    def list(self, request, *args, **kwargs):
        """List all boards accessible to the current user, including their members and tasks.

        Returns:
            Response: Return all accessible boards with their members and tasks.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific board by its ID, including its members and tasks.

        Returns:
            Response: Return the requested board with its members and tasks.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a board's details, including its title and members.
        Returns:
            Response: Return the updated board details.
        """
        instance = self.get_object()

        data = request.data.copy()

        if 'members' in data and isinstance(data['members'], list):
            valid_members = [
                member_id for member_id in data['members']
                if member_id is not None
            ]

            if valid_members:
                data['members'] = valid_members
            else:
                data.pop('members')

        serializer = BoardsSerializer(
            instance,
            data=data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_serializer = BoardUpdateSerializer(instance)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        """Create a new board and set the current user as the owner.
        The created board will also include the owner in its members list.

        Args:
            serializer (BoardsSerializer): The serializer instance for the board.
        """
        board = serializer.save(owner=self.request.user)

        serializer.instance = boards_with_counts(
            Boards.objects.filter(pk=board.pk)).get()

    def destroy(self, request, *args, **kwargs):
        """Delete a board if the current user is the owner.

        Returns:
            Response: Return a 204 No Content response if the board is deleted.

        Raises:
            NotFound: If the board does not exist.
            PermissionDenied: If the current user is not the owner of the board.
        """
        instance = Boards.objects.filter(pk=kwargs.get('pk')).first()

        if instance is None:  # Board existiert nicht
            raise NotFound('Board not found.')

        if instance.owner != request.user:  # Nur der Board-Owner darf löschen
            raise PermissionDenied(
                'The user must be the board owner to delete it.')

        # Damit IsBoardOwner-Permission ausgeführt wird
        self.check_object_permissions(request, instance)
        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)


class TasksViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tasks with appropriate permissions and serializers."""
    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = TasksSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.

        Returns:
            List of permission instances required for the current action.
        """
        if self.action in ['create', 'partial_update']:
            permission_classes = [IsAuthenticated, IsBoardMember]

        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsBoardOwnerOrTaskCreator]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return the serializer class for the current action.

        Returns:
            Serializer class corresponding to the current action.
        """
        if self.action in ['list', 'retrieve']:
            return TasksViewSerializer

        elif self.action == 'partial_update':
            return TaskUpdateSerializer

        return TasksSerializer

    def get_queryset(self):
        """
        Return the queryset of tasks based on the current user's permissions and action.

        Returns:
            QuerySet: Tasks accessible to the current user.
        """
        user = self.request.user

        if self.action in ['partial_update', 'destroy']:
            return Tasks.objects.all()

        return Tasks.objects.filter(Q(board__owner=user) | Q(board__members=user)).distinct()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific task by its ID, including its assignee, reviewer, and comment counts.
        
        Returns:
            Response: Return the requested task with its details.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a task's details, including its title, description, status, priority, assignee, reviewer, and due date.

        Returns:
            Response: Return the updated task details. 

        Raises:
            Response: Return a 400 Bad Request response if the board of the task is attempted to be changed.
        """
        instance = self.get_object()

        if 'board' in request.data:
            if str(request.data['board']) != str(instance.board_id):
                return Response({'error': 'Changing the board of a task is not allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Create a new task within a board, ensuring the current user is a member of the board.

        Returns:
            Response: Return the created task details.

        Raises:
            Response: Return a 400 Bad Request response if the current user is not a member of
            the board specified in the request data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(created_by=request.user)
        response_serializer = TasksViewSerializer(task)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """ Delete a task if the current user is either the creator of the task or the owner of the board.
        
        Returns:
            Response: Return a 204 No Content response if the task is deleted.

        Raises:
            NotFound: If the task does not exist.
        """
        instance = Tasks.objects.filter(pk=kwargs.get('pk')).first()

        if instance is None:  # Task existiert nicht
            raise NotFound('Task not found.')

        if (instance.created_by != request.user and instance.board.owner != request.user):
            raise PermissionDenied(
                'Only the task creator or board owner can delete this task.')

        self.check_object_permissions(request, instance)
        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailCheck(APIView):
    """API view to check if an email exists in the system and return user details if found."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Check if the provided email exists in the system and return user details if found.

        Returns:
            Response: Return user details if the email exists, or an error message if not found or invalid.
        """
        try:
            email = request.query_params.get('email')

            if not email:
                return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                validate_email(email)

            except ValidationError:
                return Response({'error': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email__iexact=email)

            except User.DoesNotExist:
                return Response({'error': 'Email not found.'}, status=status.HTTP_404_NOT_FOUND)

            data = {
                'id': user.id,
                'user_id': user.id,
                'email': user.email,
                'fullname': get_fullname(user)
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception:
            return Response({'error': 'Internal server error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MemberAssignedTasksView(generics.ListAPIView):
    """View to list tasks assigned to the current user, including their details."""
    serializer_class = TasksViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return the queryset of tasks assigned to the current user.

        Returns:
            QuerySet: Tasks assigned to the current user.
        """
        user = self.request.user

        return Tasks.objects.filter(Q(assignee=user) | Q(reviewer=user)).distinct()


class MemberReviewingTasksView(generics.ListAPIView):
    """View to list tasks where the current user is the reviewer, including their details."""
    serializer_class = TasksViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return the queryset of tasks where the current user is the reviewer.

        Returns:
            QuerySet: Tasks where the current user is the reviewer.
        """
        user = self.request.user

        return Tasks.objects.filter(reviewer=user)


class CommentsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """ViewSet for managing comments on tasks, including listing, creating, retrieving, and deleting comments."""
    serializer_class = CommentsSerializer
    permission_classes = [IsAuthenticated, IsCommentCreator]

    def get_queryset(self):
        """
        Return the queryset of comments for a specific task based on the task_id in the URL.

        Returns:
            QuerySet: Comments associated with the specified task.
        """
        task_id = self.kwargs.get('task_id')
        return Comments.objects.filter(task_id=task_id).order_by('created_at')

    def perform_create(self, serializer):
        """
        Create a new comment for a specific task, associating it with the current user as the author.

        Args:
            serializer (CommentsSerializer): The serializer instance for the comment.
        """
        task = Tasks.objects.get(pk=self.kwargs['task_id'])
        serializer.save(task=task, author=self.request.user)


def boards_with_counts(queryset=None):
    """Annotate the provided queryset of boards with counts of members and tasks.

    Args:
        queryset (QuerySet | None): The queryset of boards to annotate. If None, all boards are used.
        
    Returns:
        QuerySet: The annotated queryset of boards with member and task counts.
    """
    if queryset is None:
        queryset = Boards.objects.all()

    return queryset.annotate(
        annotated_member_count=Count('members', distinct=True),
        annotated_ticket_count=Count('tasks', distinct=True),
        annotated_tasks_to_do_count=Count(
            'tasks',
            filter=Q(tasks__status='to-do'),
            distinct=True
        ),
        annotated_tasks_high_prio_count=Count(
            'tasks',
            filter=Q(tasks__priority='high'),
            distinct=True
        )
    )
