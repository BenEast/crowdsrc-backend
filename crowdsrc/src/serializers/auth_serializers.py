# Crowdsrc imports
from crowdsrc.settings import TOKEN_EXPIRE_TIME
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *

# Django imports
from rest_framework.serializers import Serializer, ModelSerializer, CharField, SerializerMethodField
from django.db.models import Model, Q
from django.contrib.auth.models import User


class NotificationSerializer(ModelSerializer):
    notifications = SerializerMethodField()

    class Meta:
        model = User
        fields = ('notifications',)

    def get_notifications(self, obj):
        user_id = obj.id
        last_login = obj.last_login
        preferences = UserPreferences.objects.get(settings__user_id=user_id)

        notifications = []

        # Check if user wants notifications for accepted crowd_requests
        if preferences.notify_crowd_request_accept:
            accepted_requests = CrowdRequest.objects.filter(
                sender_id=user_id, is_accepted=True)

            for request in accepted_requests:
                notifications.append({
                    'is_new': request.responded >= last_login,
                    'datetime': request.responded,
                    'message': 'has accepted your crowd request! View their profile.',
                    'relative_url': '/crowd/' + request.receiver.username,
                    'user': UserListGETSerializer(request.receiver).data
                })

        # Check if user wants notifications for replies to team messages
        if preferences.notify_message_replies:
            new_replies = TeamMessageReply.objects.filter(
                message__user_id=user_id).exclude(user_id=user_id)

            for reply in new_replies:
                notifications.append({
                    'is_new': reply.created >= last_login,
                    'datetime': reply.created,
                    'message': 'has written a reply to your message!',
                    'relative_url': '/src/' + str(message.project_id),
                    'user': UserListGETSerializer(reply.user).data
                })

        # Check if user wants notifications for messages on their projects
        if preferences.notify_project_messages:
            new_messages = TeamMessage.objects.filter(
                project__user_id=user_id).exclude(user_id=user_id)

            for message in new_messages:
                notifications.append({
                    'is_new': message.created >= last_login,
                    'datetime': message.created,
                    'message': 'has written a message on your project!',
                    'relative_url': '/src/' + str(message.project_id),
                    'user': UserListGETSerializer(message.user).data
                })

            new_replies = TeamMessageReply.objects.filter(
                message__project__user_id=user_id).exclude(user_id=user_id)

            for reply in new_replies:
                notifications.append({
                    'is_new': reply.created >= last_login,
                    'datetime': reply.created,
                    'message': 'has written a reply to a message on your project!',
                    'relative_url': '/src/' + str(reply.message.project_id),
                    'user': UserListGETSerializer(reply.user).data
                })

        # Check if user wants notifications for submissions to their projects
        if preferences.notify_project_submissions:
            new_submissions = TaskSubmission.objects.filter(
                task__project__user_id=user_id).exclude(user_id=user_id)

            for submission in new_submissions:
                notifications.append({
                    'is_new': submission.created >= last_login,
                    'datetime': submission.created,
                    'message': 'A user has made a submission for one of your tasks!',
                    'relative_url': '/src/' + str(submission.task.project_id) + '?tab=tasks',
                    'user': None
                })

            updated_submissions = TaskSubmission.objects.filter(
                task__project__user_id=user_id).exclude(user_id=user_id)

            for submission in updated_submissions:
                notifications.append({
                    'is_new': submission.last_updated >= last_login,
                    'datetime': submission.last_updated,
                    'message': 'A user has updated their submission for one of your tasks!',
                    'relative_url': '/src/' + str(submission.task.project_id) + '?tab=tasks',
                    'user': None
                })

        # Check if user wants notifications for status changes to tasks they've saved
        if preferences.notify_saved_task_status:
            user_saved_tasks = list(UserTask.objects.only('task_id').filter(
                user_id=user_id).distinct().values_list('task_id', flat=True))

            updated_tasks = Task.objects.filter(id__in=user_saved_tasks)

            for task in updated_tasks:
                notifications.append({
                    'is_new': task.last_updated >= last_login,
                    'datetime': task.last_updated,
                    'message': 'One of your saved tasks has been updated!',
                    'relative_url': '/src/' + str(task.project_id) + '?tab=tasks',
                    'user': None
                })

        # Check if user wants notifications for changes to the status of their submissions
        if preferences.notify_submission_status:
            for submission in TaskSubmission.objects.filter(user_id=user_id):
                if submission.is_accepted:
                    message = 'Your submission has been chosen to complete a task!'
                else:
                    message = 'Your submission is no longer chosen to complete a task!'

                notifications.append({
                    'is_new': submission.accepted_date >= last_login,
                    'datetime': submission.accepted_date,
                    'message': message,
                    'relative_url': '/src/' + str(submission.task.project_id) + '?tab=tasks',
                    'user': None
                })

        return sorted(notifications, key=lambda entry: entry['datetime'], reverse=True)


class RefreshableExpiringTokenSerializer(ModelSerializer):
    crowd_requests = SerializerMethodField()
    expires = SerializerMethodField('get_expiration')
    notification_count = SerializerMethodField()
    user = UserListGETSerializer()

    class Meta:
        model = RefreshableExpiringToken
        fields = ('key', 'expires', 'refresh_token', 'refresh_expires',
                  'user', 'crowd_requests', 'notification_count')

    # Get crowd requests where user is the receiver
    def get_crowd_requests(self, obj):
        return CrowdRequest.objects.filter(receiver_id=obj.user_id).exclude(
            Q(is_accepted=True) | Q(is_rejected=True)).count()

    # Get datetime that the token expires
    def get_expiration(self, obj):
        return obj.created + TOKEN_EXPIRE_TIME

    def get_notification_count(self, obj):
        user_id = obj.user.id
        last_login = obj.user.last_login
        preferences = UserPreferences.objects.get(settings__user_id=user_id)

        count = 0

        # Check if user wants notifications for accepted crowd_requests
        if preferences.notify_crowd_request_accept:
            accepted_requests = CrowdRequest.objects.filter(
                sender_id=user_id, is_accepted=True, responded__gte=last_login)
            count += accepted_requests.count()

        # Check if user wants notifications for replies to team messages
        if preferences.notify_message_replies:
            new_replies = TeamMessageReply.objects.filter(
                message__user_id=user_id, created__gte=last_login).exclude(user_id=user_id)
            count += new_replies.count()

        # Check if user wants notifications for messages on their projects
        if preferences.notify_project_messages:
            new_messages = TeamMessage.objects.filter(
                project__user_id=user_id, created__gte=last_login).exclude(user_id=user_id)
            count += new_messages.count()

            new_replies = TeamMessageReply.objects.filter(
                message__project__user_id=user_id, created__gte=last_login).exclude(user_id=user_id)
            count += new_replies.count()

        # Check if user wants notifications for submissions to their projects
        if preferences.notify_project_submissions:
            submissions = TaskSubmission.objects.filter(task__project__user_id=user_id).filter(
                Q(created__gte=last_login) | Q(last_updated__gte=last_login)).exclude(user_id=user_id)
            count += submissions.count()

        # Check if user wants notifications for status changes to tasks they've saved
        if preferences.notify_saved_task_status:
            user_saved_tasks = list(UserTask.objects.only('task_id').filter(
                user_id=user_id).distinct().values_list('task_id', flat=True))

            updated_tasks = Task.objects.filter(
                id__in=user_saved_tasks, last_updated__gte=last_login)
            count += updated_tasks.count()

        # Check if user wants notifications for changes to the status of their submissions
        if preferences.notify_submission_status:
            submissions = TaskSubmission.objects.filter(
                user_id=user_id, last_updated__gte=last_login)
            count += submissions.count()

        return count
