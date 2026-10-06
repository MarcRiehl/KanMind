from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardsView

# routerBoard = DefaultRouter()
# routerBoard.register(r'boards', BoardViewSet, basename='boards')

urlpatterns = [
    path('boards/', BoardsView.as_view()),
]