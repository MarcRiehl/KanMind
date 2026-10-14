from django.contrib.auth.models import User
from rest_framework import serializers

from kanban_app.models import Boards, Comments, Tasks

from .utils import get_fullname


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django users exposing a read-only full name field."""
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return get_fullname(obj)


class BoardsSerializer(serializers.ModelSerializer):
    """Serializer for board records with summary counts and member information."""
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True)

    member_count = serializers.IntegerField(
        source='annotated_member_count',
        read_only=True
    )
    ticket_count = serializers.IntegerField(
        source='annotated_ticket_count',
        read_only=True
    )
    tasks_to_do_count = serializers.IntegerField(
        source='annotated_tasks_to_do_count',
        read_only=True
    )
    tasks_high_prio_count = serializers.IntegerField(
        source='annotated_tasks_high_prio_count',
        read_only=True
    )

    class Meta:
        model = Boards
        fields = ['id', 'title', 'members', 'member_count', 'ticket_count',
                  'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id']
        read_only_fields = ['id', 'owner_id']


class TasksViewSerializer(serializers.ModelSerializer):
    """Serializer for task details with nested assignee, reviewer, and comment counts."""
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    comments_count = serializers.IntegerField(
        source='comments.count', read_only=True)

    class Meta:
        model = Tasks
        fields = ['id', 'board', 'title', 'description', 'status',
                  'priority', 'assignee', 'reviewer', 'due_date', 'comments_count']


class TasksSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks while validating assignment membership against the board."""
    assignee_id = serializers.PrimaryKeyRelatedField(
        source='assignee',
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )

    reviewer_id = serializers.PrimaryKeyRelatedField(
        source='reviewer',
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )

    class Meta:
        model = Tasks
        fields = [
            'id', 'board', 'title', 'description',
            'status', 'priority', 'assignee_id',
            'reviewer_id', 'due_date', 'created_by'
        ]
        read_only_fields = ['id', 'created_by']

    def validate(self, attrs):
        board = attrs.get('board')
        assignee = attrs.get('assignee')
        reviewer = attrs.get('reviewer')

        if board is not None:
            validate_task_assignments(board, assignee, reviewer)

        return attrs


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating tasks.

    Allows updating task fields, including the assignee and reviewer.
    User data is returned as nested objects, while assignee_id and
    reviewer_id are used to assign users by their primary keys.
    Both assignments are optional and can be set to null.
    """

    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    assignee_id = serializers.PrimaryKeyRelatedField(
        source='assignee',
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )

    reviewer_id = serializers.PrimaryKeyRelatedField(
        source='reviewer',
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )

    class Meta:
        model = Tasks
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'assignee_id', 'reviewer', 'reviewer_id',
            'due_date'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        """
        Validates the task assignments before updating a task.

        Uses the existing assignee and reviewer if they are not
        included in the request data. Checks whether the assignments
        are valid for the task's board.

        Args:
            attrs (dict): The validated task data.

        Returns:
            dict: The validated task data.

        Raises:
            serializers.ValidationError: If the task assignments
                are not valid for the board.
        """
        instance = self.instance
        board = instance.board

        assignee = attrs.get('assignee', instance.assignee)
        reviewer = attrs.get('reviewer', instance.reviewer)

        validate_task_assignments(board, assignee, reviewer)

        return attrs


class BoardTaskSerializer(serializers.ModelSerializer):
    """Serializer for tasks within a board view, including assignee, reviewer, and comment counts."""
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    comments_count = serializers.IntegerField(
        source='comments.count', read_only=True)

    class Meta:
        model = Tasks
        fields = ['id', 'title', 'description', 'status', 'priority',
                  'assignee', 'reviewer', 'due_date', 'comments_count']


class BoardViewSerializer(serializers.ModelSerializer):
    """Serializer for board details including members and tasks."""
    members = UserSerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Boards
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for reading board ownership and member details in update views."""
    owner_data = UserSerializer(source='owner', read_only=True)
    members_data = UserSerializer(
        source='members', many=True, read_only=True)

    class Meta:
        model = Boards
        fields = ['id', 'title', 'owner_data', 'members_data']


class CommentsSerializer(serializers.ModelSerializer):
    """Serializer for comments including the author's full name and content."""
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comments
        fields = ['id', 'created_at', 'author', 'content']
        read_only_fields = ['id', 'created_at', 'author']

    def get_author(self, obj):
        return get_fullname(obj.author)


def validate_task_assignments(board, assignee, reviewer):
    """Ensure the assignee and reviewer belong to the board.

    Args:
        board (Boards): The board the task belongs to.
        assignee (User | None): The user assigned to the task, if any.
        reviewer (User | None): The user reviewing the task, if any.

    Raises:
        serializers.ValidationError: If the assignee is not the board owner
            or a board member.
        serializers.ValidationError: If the reviewer is not the board owner
            or a board member.
    """
    if assignee is not None:
        if not (
            board.owner_id == assignee.pk
            or board.members.filter(pk=assignee.pk).exists()
        ):
            raise serializers.ValidationError({
                'assignee_id': 'The assignee must be a member of the board.'
            })

    if reviewer is not None:
        if not (
            board.owner_id == reviewer.pk
            or board.members.filter(pk=reviewer.pk).exists()
        ):
            raise serializers.ValidationError({
                'reviewer_id': 'The reviewer must be a member of the board.'
            })
