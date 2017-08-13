from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

class Category(models.Model):
    # Required Fields
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()

class Project(models.Model):
    # Required Fields
    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, related_name='projects')
    category = models.ForeignKey(Category, related_name='projects')
    description = models.TextField()
    create_datetime = models.DateTimeField(default=datetime.now, blank=True, editable=False)

    # Optional Fields
    website = models.CharField(max_length=2083, blank=True)

class Profile(models.Model):
    # Required Fields
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Optional Fields
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    image_name = models.CharField(max_length=200, blank=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

class Comment(models.Model):
    # Required Fields
    user = models.ForeignKey(User, related_name='comments')
    project = models.ForeignKey(Project, related_name='comments')
    comment_body = models.TextField()
    create_datetime = models.DateTimeField(default=datetime.now, blank=True, editable=False)

class Team(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='team')

    @receiver(post_save, sender=Project)
    def create_team(sender, instance, created, **kwargs):
        if created:
            Team.objects.create(project=instance)

    @receiver(post_save, sender=Project)
    def save_team(sender, instance, **kwargs):
        instance.team.save()

class TeamMember(models.Model):
    team = models.ForeignKey(Team, related_name='members')
    user = models.ForeignKey(User, related_name='members')
    role = models.CharField(default='member', max_length=15)

class TeamMessage(models.Model):
    team = models.ForeignKey(Team, related_name='messages')
    user = models.ForeignKey(User, related_name='messages')
    title = models.CharField(max_length=300)
    body = models.TextField()
    create_datetime = models.DateTimeField(default=datetime.now, blank=True, editable=False)

class Reply(models.Model):
    user = models.ForeignKey(User, related_name='replies')
    teamMessage = models.ForeignKey(TeamMessage, related_name='replies')
    body = models.TextField()
    create_datetime = models.DateTimeField(default=datetime.now, blank=True, editable=False)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
