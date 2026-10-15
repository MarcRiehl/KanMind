from rest_framework.exceptions import NotFound
from rest_framework.permissions import SAFE_METHODS, BasePermission

from ..models import Boards, Tasks


class IsBoardOwnerOrTaskCreator(BasePermission):
    """
    Custom permission to control access to tasks based on board membership,
    task creation, and board ownership.
    """

    def has_permission(self, request, view):
        """
        Check whether the user is allowed to create a task on a board.

        Args:
            request (Request): The HTTP request.
            view (View): The view being accessed.

        Returns:
            bool: True if the request is permitted, otherwise False.
        """
        if view.action == 'create':
            board_id = request.data.get('board')

            if not board_id:
                return True

            board = Boards.objects.filter(pk=board_id).first()

            if board is None:
                return True

            return (
                board.owner == request.user
                or board.members.filter(pk=request.user.pk).exists()
            )

        return True

    def has_object_permission(self, request, view, obj):
        """
        Check whether the user can access or modify a specific task.

        Safe methods are allowed for all users who reach this check.
        DELETE is allowed only for the task creator or board owner.
        Other write methods are denied.

        Args:
            request (Request): The HTTP request.
            view (View): The view being accessed.
            obj (Model): The task being accessed.

        Returns:
            bool: True if the action is permitted, otherwise False.
        """
        if request.method in SAFE_METHODS:
            return True

        if request.method == 'DELETE':
            return (
                obj.created_by == request.user
                or obj.board.owner == request.user
            )

        return False


class IsBoardOwnerOrMember(BasePermission):
    """
    Custom permission to allow board owners and members to access a board.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check whether the user owns or is a member of the board.

        Args:
            request (Request): The HTTP request.
            view (View): The view being accessed.
            obj (Model): The board being accessed.

        Returns:
            bool: True if the user owns or is a member of the board,
                otherwise False.
        """
        return (
            obj.owner == request.user
            or obj.members.filter(pk=request.user.pk).exists()
        )


class IsCommentCreator(BasePermission):
    """
    Custom permission to restrict comment access to board members
    and allow only comment authors to delete comments.
    """

    def has_permission(self, request, view):
        """
        Check whether the user is a member of the task's board.

        Args:
            request (Request): The HTTP request.
            view (View): The view being accessed.

        Returns:
            bool: True if the task exists and the user is a board member,
                otherwise False.
        """
        task_id = view.kwargs.get('task_id')

        task = Tasks.objects.filter(pk=task_id).select_related('board').first()

        if task is None:
            return False

        return task.board.members.filter(pk=request.user.pk).exists()

    def has_object_permission(self, request, view, obj):
        """
        Check whether the user can access or delete a specific comment.

        Comment authors can delete their own comments.
        Safe methods are allowed for users who pass the general permission check.
        Other methods are denied.

        Args:
            request (Request): The HTTP request.
            view (View): The view being accessed.
            obj (Model): The comment being accessed.

        Returns:
            bool: True if the request method is allowed, otherwise False.
        """
        if request.method == 'DELETE':
            return obj.author_id == request.user.id  # darf nur der #Kommentar autor

        if request.method in ('GET', 'HEAD', 'OPTIONS'):  # Mitglieder dürfen lesen
            return True

        return False

class IsBoardOwner(BasePermission):
    """
    Custom permission to allow only the board owner to access a board.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check whether the current user owns the board.

        Args:
            request (Request): The HTTP request.
            view (View): The view being accessed.
            obj (Model): The board being accessed.

        Returns:
            bool: True if the user is the board owner, otherwise False.
        """
        return obj.owner == request.user

class IsBoardMember(BasePermission):
    """
    Custom permission to allow board owners and members to access tasks.
    """

    def has_permission(self, request, view):
        """
        Check whether the user can create a task on the specified board.

        For other actions, this method grants permission without further checks.

        Args:
            request (Request): The HTTP request.
            view (View): The view being accessed.

        Returns:
            bool: True if the user is the board owner or a member when
                creating a task, or if the action is not 'create'.
        """
        if view.action == 'create':
            board_id = request.data.get('board')

            if not board_id:
                return False

            board = Boards.objects.filter(pk=board_id).first()

            if board is None:
                raise NotFound("Board not found.")

            return (
                board.owner_id == request.user.pk
                or board.members.filter(pk=request.user.pk).exists()
            )

        return True

    def has_object_permission(self, request, view, obj):
        """
        Check whether the user owns or is a member of the task's board.

        Args:
            request (Request): The HTTP request.
            view (View): The view being accessed.
            obj (Model): The task being accessed.

        Returns:
            bool: True if the user owns or is a member of the board,
                otherwise False.
        """
        return (
            obj.board.owner_id == request.user.pk
            or obj.board.members.filter(pk=request.user.pk).exists()
        )