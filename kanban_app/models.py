from django.contrib.auth.models import User
from django.db import models


class Boards(models.Model):
    """Model representing a board with members and task counts."""
    title = models.CharField(max_length=100)
    members = models.ManyToManyField(
        User, related_name='member_boards', blank=True)
    ticket_count = models.IntegerField(default=0)
    tasks_to_do_count = models.IntegerField(default=0)
    tasks_high_prio_count = models.IntegerField(default=0)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_boards')

    def __str__(self):
        return self.title


class Tasks(models.Model):
    """Model representing a task with status, priority, and associated users."""
    board = models.ForeignKey(
        Boards, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=100)
    description = models.TextField()

    class Status(models.TextChoices):
        TODO = 'to-do'
        IN_PROGRESS = 'in-progress'
        REVIEW = 'review'
        DONE = 'done'

    class Priority(models.TextChoices):
        LOW = 'low'
        MEDIUM = 'medium'
        HIGH = 'high'
    status = models.CharField(max_length=20, choices=Status.choices)
    priority = models.CharField(max_length=20, choices=Priority.choices)
    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    reviewer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_tasks')
    due_date = models.DateField()
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_tasks')

    def __str__(self):
        return self.title


class Comments(models.Model):
    """Model representing a comment on a task with an author and timestamp."""
    task = models.ForeignKey(
        Tasks, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(
        auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()

    def __str__(self):
        return f'Comment by {self.author.username}'
