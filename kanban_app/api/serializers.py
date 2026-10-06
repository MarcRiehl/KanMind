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

