from rest_framework import serializers
from kanban_app.models import Boards, Tasks, Comments
from django.contrib.auth.models import User

class BoardsSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), write_only=True) #bei write_only=True wird das Feld nicht angezeigt
    member_count = serializers.SerializerMethodField() #Gibt Anzahl der Members von einem Board zurück

    class Meta:
        model = Boards
        fields = ['id', 'title', 'members', 'member_count', 'ticket_count', 'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id']
        read_only_fields = ['id', 'ticket_count', 'tasks_to_do_count' , 'tasks_high_prio_count', 'owner_id']

    def get_member_count(self, obj):
        return obj.members.count()


class UserSerializer(serializers.ModelSerializer):

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip()
    
class TasksViewSerializer(serializers.ModelSerializer):

    assignee = UserSerializer(read_only=True) #macht Probleme muss noch gelöst werden, da sonst das Feld nicht funktioniert
    reviewer = UserSerializer(read_only=True)

    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Tasks
        fields = ['id', 'board', 'title', 'description', 'status', 'priority', 'assignee', 'reviewer', 'due_date', 'comments_count']

class TasksSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tasks
        fields = ['id', 'board', 'title', 'description', 'status', 'priority', 'assignee', 'reviewer', 'due_date', 'created_by']

        read_only_fields = ['id', 'created_by']

