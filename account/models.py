from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from account.manager import CustomUserManager

import datetime
import os



# from multiselectfield import MultiSelectField

class UserType(models.Model):
    user_type = models.CharField(max_length=15, blank=False, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user_type

class User(AbstractUser):
    username = None
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE)
    email = models.EmailField(unique=True, blank=False, error_messages={
        'required': "User_type must be defined",
        'unique': "A user already exist"
    })
    phone = models.CharField(max_length=18, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True) 


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    # def get_absolute_url(self):
    #     return reverse('meditech_admin:client_detail', args=[str(self.id)])

class UsersSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prefered_view = models.CharField(max_length=10, blank=False, null=False, default='mobile')
    using_hand = models.CharField(max_length=10, blank=False, null=False, default='right')
    reminder_time = models.CharField(max_length=5, blank=True, null=True, default='21:00')
    reminder_enabled = models.BooleanField(default=False)

    def __int__(self):
        return self.id


class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.endpoint[:30]}..."
