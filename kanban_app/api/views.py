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
    """
    ViewSet for managing boards with action-specific serializers
    and permission checks.
    """

    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = BoardsSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Return the permission instances required for the current action.

        Returns:
            list: Permission instances configured for the current action.
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
            type: BoardViewSerializer for retrieving a board,
                otherwise BoardsSerializer.
        """
        if self.action == 'retrieve':
            return BoardViewSerializer

        return BoardsSerializer

    def get_queryset(self):
        """
        Return boards based on the current action and user.

        For partial updates and deletions, return all boards.
        For other actions, return boards owned by or assigned to the user,
        including calculated task counts.

        Returns:
            QuerySet: The boards matching the current action's queryset.
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
        """
        Return all accessible boards with their members and tasks.

        Returns:
            Response: HTTP 200 response containing the serialized boards.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        Return a specific board with its members and tasks.

        Returns:
            Response: HTTP 200 response containing the serialized board.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a board's details and membership.

        Returns:
            Response: HTTP 200 response containing the updated board details.
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
        """
        Create a board and assign the current user as its owner.

        Args:
            serializer (BoardsSerializer): The serializer used to create the board.
        """
        board = serializer.save(owner=self.request.user)

        serializer.instance = boards_with_counts(
            Boards.objects.filter(pk=board.pk)).get()

    def destroy(self, request, *args, **kwargs):
        """
        Delete a board if the current user is its owner.

        Returns:
            Response: HTTP 204 response if the board is deleted.

        Raises:
            NotFound: If the board does not exist.
            PermissionDenied: If the current user is not the board owner.
        """
        instance = Boards.objects.filter(pk=kwargs.get('pk')).first()

        if instance is None:
            raise NotFound('Board not found.')

        if instance.owner != request.user:
            raise PermissionDenied(
                'The user must be the board owner to delete it.')

        self.check_object_permissions(request, instance)
        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)


class TasksViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tasks with action-specific permissions and serializers."""

    http_method_names = ['get', 'post', 'patch', 'delete']

    serializer_class = TasksSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Return the permission instances required for the current action.

        Returns:
            list: Permission instances configured for the current action.
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
            type: TasksViewSerializer for list and retrieve actions,
                TaskUpdateSerializer for partial updates, or
                TasksSerializer for other actions.
        """
        if self.action in ['list', 'retrieve']:
            return TasksViewSerializer

        elif self.action == 'partial_update':
            return TaskUpdateSerializer

        return TasksSerializer

    def get_queryset(self):
        """
        Return tasks based on the current action and user's board access.

        Return all tasks for partial updates and deletions.
        For other actions, return tasks belonging to boards owned by
        or accessible to the current user.

        Returns:
            QuerySet: Tasks matching the current action's queryset.
        """
        user = self.request.user

        if self.action in ['partial_update', 'destroy']:
            return Tasks.objects.all()

        return Tasks.objects.filter(
            Q(board__owner=user) | Q(board__members=user)
        ).distinct()

    def retrieve(self, request, *args, **kwargs):
        """
        Return a specific task with its assignee, reviewer, and comment count.

        Returns:
            Response: HTTP 200 response containing the serialized task.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a task's fields without changing its board.

        Returns:
            Response: HTTP 200 response containing the updated task,
                or HTTP 400 if an attempt is made to change its board.
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
        """
        Create a task and assign the current user as its creator.

        Returns:
            Response: HTTP 201 response containing the created task.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(created_by=request.user)
        response_serializer = TasksViewSerializer(task)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a task if the current user created it or owns its board.

        Returns:
            Response: HTTP 204 response if the task is deleted.

        Raises:
            NotFound: If the task does not exist.
            PermissionDenied: If the current user is neither the task
                creator nor the board owner.
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
    """
    API view to validate an email address and retrieve the corresponding user's details.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Validate an email address and return the corresponding user details.

        Returns:
            Response: HTTP 200 with user details if found, HTTP 400 if the
                email is missing or invalid, HTTP 404 if no user is found,
                or HTTP 500 if an unexpected error occurs.
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
    """
    View to list tasks assigned to or reviewed by the current user.
    """

    serializer_class = TasksViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return tasks assigned to or reviewed by the current user.

        Returns:
            QuerySet: Tasks where the current user is the assignee or reviewer.
        """
        user = self.request.user

        return Tasks.objects.filter(
            Q(assignee=user) | Q(reviewer=user)
        ).distinct()


class MemberReviewingTasksView(generics.ListAPIView):
    """View to list tasks reviewed by the current user."""

    serializer_class = TasksViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return tasks for which the current user is the reviewer.

        Returns:
            QuerySet: Tasks assigned to the current user as reviewer.
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
    """
    ViewSet for listing, creating, retrieving, and deleting task comments.
    """
    serializer_class = CommentsSerializer
    permission_classes = [IsAuthenticated, IsCommentCreator]

    def get_queryset(self):
        """
        Return comments for a specific task, ordered by creation date.

        Returns:
            QuerySet: Comments belonging to the task specified by task_id.
        """
        task_id = self.kwargs.get('task_id')
        return Comments.objects.filter(task_id=task_id).order_by('created_at')

    def perform_create(self, serializer):
        """
        Save a comment with the specified task and current user as author.

        Args:
            serializer (CommentsSerializer): The serializer used to create the comment.
        """
        task = Tasks.objects.get(pk=self.kwargs['task_id'])
        serializer.save(task=task, author=self.request.user)


def boards_with_counts(queryset=None):
    """
    Annotate boards with counts of members, tasks, to-do tasks, and high-priority tasks.

    Args:
        queryset (QuerySet | None): The boards to annotate.
            If None, all boards are used.

    Returns:
        QuerySet: The annotated boards with calculated member and task counts.
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
