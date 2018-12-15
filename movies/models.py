from random import randint
from django.db import models

class Movie(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    tmdb_id = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.name
