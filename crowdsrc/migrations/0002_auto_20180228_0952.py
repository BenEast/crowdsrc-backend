# Generated by Django 2.0.2 on 2018-02-28 15:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crowdsrc', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpreferences',
            name='notify_crowd_request_accept',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='notify_message_replies',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='notify_project_messages',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='notify_project_submissions',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='notify_saved_task_status',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='notify_submission_status',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='review_submission_level',
            field=models.IntegerField(blank=True, default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)]),
        ),
    ]
