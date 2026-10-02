from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Board(models.Model):
    title = models.CharField(max_length=100)
    member_count = models.JSONField()
    ticket_count = models.IntegerField()
    tasks_to_do_count = models.IntegerField()
    tasks_high_prio_count = models.IntegerField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
