from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    avatar = models.ImageField(upload_to='users', null=True, blank=True, default='users/anonimuser.jpg')
    bio = models.TextField('Biography', null=True, blank=True)
    
    def __str__(self):
        return self.username

