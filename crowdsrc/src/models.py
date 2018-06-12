import os

# Crowdsrc imports
from crowdsrc.settings import *

# Django imports
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework_jwt.settings import api_settings


def refresh_token_expire():
    return timezone.now() + REFRESH_TOKEN_EXPIRE_TIME


class RefreshableExpiringToken(Token):
    refresh_token = models.CharField(max_length=255, unique=True)
    refresh_expires = models.DateTimeField(
        default=refresh_token_expire, blank=True, editable=False)


class BlockedUser(models.Model):
    # Required Fields
    source = models.ForeignKey(
        User, related_name='blocked_users', on_delete=models.CASCADE)
    target = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)

    class Meta:
        unique_together = ('source', 'target')
        ordering = ('target__username', 'created')


class UserSettings(models.Model):
    user = models.OneToOneField(
        User, related_name='settings', on_delete=models.CASCADE)

    @receiver(post_save, sender=User)
    def create_user_settings(sender, instance, created, **kwargs):
        if created:
            UserSettings.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_settings(sender, instance, **kwargs):
        instance.settings.save()


class UserPreferences(models.Model):
    settings = models.OneToOneField(
        UserSettings, related_name='preferences', on_delete=models.CASCADE)

    # Notification settings
    notify_crowd_request_accept = models.BooleanField(default=True, blank=True)
    notify_message_replies = models.BooleanField(default=True, blank=True)
    notify_project_messages = models.BooleanField(default=True, blank=True)
    notify_project_submissions = models.BooleanField(default=True, blank=True)
    notify_saved_task_status = models.BooleanField(default=True, blank=True)
    notify_submission_status = models.BooleanField(default=True, blank=True)

    @receiver(post_save, sender=UserSettings)
    def create_user_preferences(sender, instance, created, **kwargs):
        if created:
            UserPreferences.objects.create(settings=instance)

    @receiver(post_save, sender=UserSettings)
    def save_user_preferences(sender, instance, **kwargs):
        instance.preferences.save()


class UserPrivacySettings(models.Model):
    settings = models.OneToOneField(
        UserSettings, related_name='privacy', on_delete=models.CASCADE)

    allow_email_search = models.BooleanField(default=True, blank=True)
    allow_loc_search = models.BooleanField(default=True, blank=True)
    allow_name_search = models.BooleanField(default=True, blank=True)
    allow_username_search = models.BooleanField(default=True, blank=True)

    view_activity_level = models.IntegerField(default=MIN_USER_PERMISSION, blank=True,
                                              validators=[MinValueValidator(MIN_USER_PERMISSION),
                                                          MaxValueValidator(MAX_USER_PERMISSION)])

    view_age_level = models.IntegerField(default=MIN_USER_PERMISSION, blank=True,
                                         validators=[MinValueValidator(MIN_USER_PERMISSION),
                                                     MaxValueValidator(MAX_USER_PERMISSION)])

    view_email_level = models.IntegerField(default=MIN_USER_PERMISSION, blank=True,
                                           validators=[MinValueValidator(MIN_USER_PERMISSION),
                                                       MaxValueValidator(MAX_USER_PERMISSION)])

    view_crowd_level = models.IntegerField(default=MIN_USER_PERMISSION, blank=True,
                                           validators=[MinValueValidator(MIN_USER_PERMISSION),
                                                       MaxValueValidator(MAX_USER_PERMISSION)])

    view_stats_level = models.IntegerField(default=MIN_USER_PERMISSION, blank=True,
                                           validators=[MinValueValidator(MIN_USER_PERMISSION),
                                                       MaxValueValidator(MAX_USER_PERMISSION)])

    @receiver(post_save, sender=UserSettings)
    def create_user_privacy_settings(sender, instance, created, **kwargs):
        if created:
            UserPrivacySettings.objects.create(settings=instance)

    @receiver(post_save, sender=UserSettings)
    def save_user_privacy_settings(sender, instance, **kwargs):
        instance.privacy.save()


class Project(models.Model):
    # Required Fields
    title = models.CharField(max_length=300)
    user = models.ForeignKey(
        User, related_name='projects', on_delete=models.CASCADE)
    description = models.TextField()
    created = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)
    last_updated = models.DateTimeField(default=timezone.now, blank=True)

    # Optional Fields
    website = models.CharField(max_length=2083, blank=True)

    class Meta:
        ordering = ('created', 'title', 'id')


def profile_image_upload_to(instance, filename):
    return os.path.join(os.path.join(USER_IMAGE_ROOT, str(instance.user_id)), filename)


class Profile(models.Model):
    # Required Fields
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    created = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)
    last_updated = models.DateTimeField(default=timezone.now, blank=True)

    # Optional Fields
    bio = models.TextField(blank=True, default='')
    location = models.CharField(max_length=30, blank=True, default='Unknown')
    birth_date = models.DateField(blank=True, null=True)
    image = models.ImageField(
        upload_to=profile_image_upload_to, blank=True,
        default=os.path.join(USER_IMAGE_ROOT, 'default.png'))

    # Field to store email before verification (if updating email)
    pending_email = models.EmailField(blank=True, null=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()


class TeamMessage(models.Model):
    project = models.ForeignKey(
        Project, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, related_name='messages', on_delete=models.CASCADE)
    body = models.TextField()
    created = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)
    last_updated = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        ordering = ('-created', 'id')


class Task(models.Model):
    # Required Fields
    project = models.ForeignKey(
        Project, related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    description = models.TextField()
    status_level = models.IntegerField(default=MIN_TASK_STATUS, blank=True,
                                       validators=([MinValueValidator(MIN_TASK_STATUS),
                                                    MaxValueValidator(MAX_TASK_STATUS)]))
    created = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)
    last_updated = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        ordering = ('title', '-last_updated', '-created')


class UserTask(models.Model):
    task = models.ForeignKey(
        Task, related_name='saved_users', on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, related_name='saved_tasks', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('task', 'user')


class TaskSubmission(models.Model):
    task = models.ForeignKey(
        Task, related_name='submissions', on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, related_name='submissions', on_delete=models.CASCADE)
    created = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)
    last_updated = models.DateTimeField(default=timezone.now, blank=True)
    is_accepted = models.BooleanField(default=False, blank=True)
    accepted_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('task', 'user')


def submission_upload_to(instance, filename):
    return TASK_SUBMISSION_ROOT + '/{}/{}/{}'.format(
        instance.submission.task_id, instance.submission_id, filename)


class SubmissionFile(models.Model):
    submission = models.ForeignKey(
        TaskSubmission, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to=submission_upload_to)


class SubmissionReview(models.Model):
    submission = models.ForeignKey(
        TaskSubmission, related_name='reviews', on_delete=None)
    reviewer = models.ForeignKey(User, related_name='reviews', on_delete=None)
    created = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)
    rating = models.IntegerField(validators=(
        [MinValueValidator(0), MaxValueValidator(10)]))

    class Meta:
        unique_together = ('submission', 'reviewer')


class Skill(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ('name', 'id')


class SubmissionSkillReview(models.Model):
    review = models.ForeignKey(
        SubmissionReview, related_name='skills', on_delete=models.CASCADE)
    skill = models.ForeignKey(
        Skill, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(validators=(
        [MinValueValidator(0), MaxValueValidator(10)]))

    class Meta:
        unique_together = ('review', 'skill')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        refresh_token = api_settings.JWT_ENCODE_HANDLER(
            api_settings.JWT_PAYLOAD_HANDLER(instance))
        RefreshableExpiringToken.objects.create(
            user=instance, refresh_token=refresh_token)


class TaskSkill(models.Model):
    task = models.ForeignKey(
        Task, related_name='skills', on_delete=models.CASCADE)
    skill = models.ForeignKey(
        Skill, related_name='tasks', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('task', 'skill')
        ordering = ('skill__name', 'id')


class UserSkill(models.Model):
    user = models.ForeignKey(
        User, related_name='skills', on_delete=models.CASCADE)
    skill = models.ForeignKey(
        Skill, related_name='users', on_delete=models.CASCADE)
    is_preferred = models.BooleanField(blank=True, default=True)

    class Meta:
        unique_together = ('user', 'skill')
        ordering = ('skill__name', 'id')


class Category(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ('name',)


class ProjectCategory(models.Model):
    project = models.ForeignKey(
        Project, related_name='categories', on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category, related_name='projects', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('project', 'category')


class TeamMessageReply(models.Model):
    message = models.ForeignKey(
        TeamMessage, related_name='replies', on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, related_name='message_replies', on_delete=models.CASCADE)
    body = models.TextField()
    created = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)
    last_updated = models.DateTimeField(default=timezone.now, blank=True)


class CrowdRequest(models.Model):
    sender = models.ForeignKey(
        User, related_name='sent_crowd_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(
        User, related_name='received_crowd_requests', on_delete=models.CASCADE)

    created = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)
    responded = models.DateTimeField(default=timezone.now, blank=True)

    is_accepted = models.BooleanField(default=False, blank=True)
    is_rejected = models.BooleanField(default=False, blank=True)
    is_viewed = models.BooleanField(default=False, blank=True)

    class Meta:
        unique_together = (('sender', 'receiver'), ('receiver', 'sender'))
