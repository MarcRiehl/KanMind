from rest_framework.permissions import BasePermission, SAFE_METHODS
from ..models import Tasks, Boards

class IsBoardOwnerOrTaskCreator(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            board_id = request.data.get('board')

            if not board_id: #Fehlende oder ungültige Board-ID
                return True

            board = Boards.objects.filter(pk=board_id).first()

            if board is None: #kein Board vorhanden
                return True
            
            return (board.owner == request.user or board.members.filter(pk=request.user.pk).exists())  #darf nur der Member und Owner

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.method == 'DELETE': #darf nur der Creator und Owner
            return (obj.created_by == request.user or obj.board.owner == request.user) 

        return False
        
class IsBoardOwnerOrMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (obj.owner == request.user or obj.members.filter(pk=request.user.pk).exists())#besser mit pk als allgemeine schreibweise

class IsCommentCreator(BasePermission):

    def has_permission(self, request, view):
        task_id = view.kwargs.get('task_id')

        task = Tasks.objects.filter(pk=task_id).select_related('board').first()#first() = Gibt den ersten gefundenen Task zurück oder None

        if task is None:
            return False #kein Task vorhanden
        
        return task.board.members.filter(pk=request.user.pk).exists()#Muss Mitglied des Boards sein

    def has_object_permission(self, request, view, obj):
        
        if request.method == 'DELETE':
            return obj.author_id == request.user.id #darf nur der #Kommentar autor

        if request.method in ('GET', 'HEAD', 'OPTIONS'):#Mitglieder dürfen lesen
            return True

        return False

class IsBoardOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsBoardMember(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            board_id = request.data.get('board')

            if not board_id: #Fehlende oder ungültige Board-ID
                return True

            board = Boards.objects.filter(pk=board_id).first()

            if board is None: #kein Board vorhanden
                return True

            return board.members.filter(pk=request.user.pk).exists()

        return True

    def has_object_permission(self, request, view, obj):
        return obj.board.members.filter(pk=request.user.pk).exists()