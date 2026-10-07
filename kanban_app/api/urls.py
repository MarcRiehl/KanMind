from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardsViewSet, EmailCheck, MemberAssignedTasks, MemberReviewing, TasksViewSet, CommentsViewSet

router = DefaultRouter()
router.register(r'boards', BoardsViewSet, basename='boards')
router.register(r'tasks', TasksViewSet, basename='tasks')

comments_list = CommentsViewSet.as_view({'get': 'list', 'post': 'create'})

comments_detail = CommentsViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})

urlpatterns = [
    path('tasks/assigned-to-me/', MemberAssignedTasks.as_view()),
    path('tasks/reviewing/', MemberReviewing.as_view()),
    path('tasks/<int:task_id>/comments/', comments_list, name='task-comments'),
    path('tasks/<int:task_id>/comments/<int:pk>/', comments_detail, name='task-comment-detail'),
    path('', include(router.urls)),
    path('email-check/', EmailCheck.as_view()),
]