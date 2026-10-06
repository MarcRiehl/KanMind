from rest_framework import serializers
from kanban_app.models import Boards, Tasks, Comments

class BoardsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Boards
        exclude = []