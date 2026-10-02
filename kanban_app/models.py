from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Board(models.Model):
    title = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='member_boards', blank=True)
    member_count = models.JSONField()
    ticket_count = models.IntegerField(default=0)
    tasks_to_do_count = models.IntegerField(default=0)
    tasks_high_prio_count = models.IntegerField(default=0)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
