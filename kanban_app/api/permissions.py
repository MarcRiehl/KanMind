from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsBoardOwnerOrTaskCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        elif request.method == "DELETE": #darf nur der Creator und Owner
            return (obj.created_by == request.user or obj.board.owner == request.user)
        
class IsBoardMember(BasePermission):
    pass

class IsCommentCreator(BasePermission):
    pass