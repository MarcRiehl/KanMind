from rest_framework.permissions import BasePermission, SAFE_METHODS
from ..models import Tasks

class IsBoardOwnerOrTaskCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        elif request.method == "DELETE": #darf nur der Creator und Owner
            return (obj.created_by == request.user or obj.board.owner == request.user)
        
class IsBoardOwnerOrMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (obj.owner == request.user or obj.members.filter(id=request.user.id).exists())

class IsCommentCreator(BasePermission):

    def has_permission(self, request, view):
        task_id = view.kwargs.get('task_id')

        task = Tasks.objects.filter(pk=task_id).select_related('board').first()#first() = Gibt den ersten gefundenen Task zurück oder None

        if task is None:
            return False #kein Task vorhanden
        
        return task.board.members.filter(pk=request.user.pk).exists()#Muss Mitglied des Boards sein

    def has_object_permission(self, request, view, obj):
        
        if request.method == 'DELETE':
            return obj.author_id == request.user.id #darf nur der #Kommentarautor, siehe auch

        if request.method in ('GET', 'HEAD', 'OPTIONS'):#Mitglieder dürfen lesen
            return True

        return False
