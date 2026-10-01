from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet

routerBoard = DefaultRouter()
routerBoard.register(r'boards', BoardViewSet, basename='achievement')

urlpatterns = [
    path('', include(routerBoard.urls)),
]