from rest_framework import serializers
from kanban_app.models import Boards, Tasks, Comments
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip()

class BoardsSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), write_only=True) #bei write_only=True wird das Feld nicht angezeigt
    member_count = serializers.SerializerMethodField() #Gibt Anzahl der Members von einem Board zurück
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Boards
        fields = ['id', 'title', 'members', 'member_count', 'ticket_count', 'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id']
        read_only_fields = ['id', 'ticket_count', 'tasks_to_do_count' , 'tasks_high_prio_count', 'owner_id']

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
         return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
         return obj.tasks.filter(priority="high").count()
    
class TasksViewSerializer(serializers.ModelSerializer):

    assignee = UserSerializer(read_only=True)
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

class TaskUpdateSerializer(serializers.ModelSerializer):

    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    assignee_id = serializers.PrimaryKeyRelatedField(
        source='assignee',
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )

    reviewer_id = serializers.PrimaryKeyRelatedField(
        source='reviewer',
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )

    def validate(self, attrs):
        instance = self.instance
        board = instance.board

        assignee = attrs.get('assignee', instance.assignee)#Bestehende Zuweisungen beibehalten für beide Felder, bei patch
        reviewer = attrs.get('reviewer', instance.reviewer)

        if (assignee is not None and not board.members.filter(pk=assignee.pk).exists()):
            raise serializers.ValidationError({
                'assignee_id':
                    'The assignee must be a member of the board.'
            })

        if (reviewer is not None and not board.members.filter(pk=reviewer.pk).exists()):
            raise serializers.ValidationError({
                'reviewer_id':
                    'The reviewer must be a member of the board.'
            })

        return attrs

    class Meta:
        model = Tasks
        fields = ['id', 'title', 'description', 'status', 'priority', 'assignee', 'assignee_id', 'reviewer', 'reviewer_id', 'due_date']
        read_only_fields = ['id']


class BoardTaskSerializer(serializers.ModelSerializer):

    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Tasks
        fields = ['id', 'title', 'description', 'status', 'priority', 'assignee', 'reviewer', 'due_date','comments_count']

class BoardViewSerializer(serializers.ModelSerializer):

    members = UserSerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Boards
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']

class BoardUpdateSerializer(serializers.ModelSerializer):
    owner_data = UserSerializer(source='owner', read_only=True) #Owner Feld des Boards über User Serializer
    members_data = UserSerializer(source='members', many=True, read_only=True) #Many-to-Many von Members

    class Meta:
        model = Boards
        fields = ['id', 'title', 'owner_data', 'members_data']

class CommentsSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comments
        fields = ['id', 'created_at', 'author', 'content']
        read_only_fields = ['id', 'created_at', 'author']

    def get_author(self, obj):
        return obj.author.get_full_name() or obj.author.username

