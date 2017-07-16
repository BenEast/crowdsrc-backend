from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profiles')

    # Optional Fields
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    image_name = models.CharField(max_length=200, blank=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    #@receiver(post_save, sender=User)
    #def save_user_profile(sender, instance, **kwargs):
    #    instance.profile.save()

class Comment(models.Model):
    # Required Fields
    user = models.ForeignKey(User, related_name='comments')
    project = models.ForeignKey(Project, related_name='comments')
    comment_body = models.TextField()
    create_datetime = models.DateTimeField(default=datetime.now, blank=True, editable=False)
