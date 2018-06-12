import re

# Crowdsrc imports
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from crowdsrc.settings import MIN_USER_PERMISSION, MAX_USER_PERMISSION
from .skill_serializers import UserSkillSerializer
from .task_serializers import TaskGETSerializer

# Django imports
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ValidationError, ModelSerializer, ImageField, SerializerMethodField


class UserTaskPOSTSerializer(ModelSerializer):
    class Meta:
        model = UserTask
        fields = ('task', 'user')


class UserTaskGETSerializer(ModelSerializer):
    task = SerializerMethodField(read_only=True)

    class Meta:
        model = UserTask
        fields = ('task',)

    def get_task(self, obj):
        task = Task.objects.get(id=obj.task_id)
        return TaskGETSerializer(task, context={'requester_id': obj.user_id}).data


##########################################################################
# Much love to this guy here:
# https://stackoverflow.com/questions/28036404/django-rest-framework-upload-image-the-submitted-data-was-not-a-file
##########################################################################
class Base64ImageField(ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.

    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268

    Updated for Django REST framework 3.
    """

    def to_internal_value(self, data):
        from django.core.files.base import ContentFile
        import base64
        import six
        import uuid

        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name
            file_name = str(uuid.uuid4())[:12]
            # Get the file name extension
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension


class UserImageSerializer(ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Profile
        fields = ('image',)


class UserListGETSerializer(ModelSerializer):
    in_crowd = SerializerMethodField()

    def get_in_crowd(self, obj):
        requester_id = self.context.get('requester_id')
        try:
            CrowdRequest.objects.get(Q(sender=obj, receiver_id=requester_id)
                                     | Q(sender_id=requester_id, receiver=obj))
            return True
        except:
            return False

    class Meta:
        model = User
        fields = ('id', 'username', 'in_crowd')


class ProfileGETSerializer(ModelSerializer):
    birth_date = SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('id', 'bio', 'location', 'birth_date',
                  'created', 'last_updated')

    def get_birth_date(self, obj):
        view_age_level = UserPrivacySettings.objects.get(
            settings__user_id=obj.user_id).view_age_level

        requester_id = self.context.get('requester_id')

        if view_age_level == MIN_USER_PERMISSION:
            return obj.birth_date
        elif view_age_level == MAX_USER_PERMISSION:
            if requester_id == obj.user_id:
                return obj.birth_date
            return None

        # Return birth date if requester is in user's crowd
        try:
            CrowdRequest.objects.get(Q(sender_id=obj.user_id, receiver_id=requester_id, is_accepted=True) | Q(
                sender_id=requester_id, receiver_id=obj.user_id, is_accepted=True))
            return obj.birth_date
        except:
            return None


class UserSearchSerializer(ModelSerializer):
    email = SerializerMethodField(read_only=True)
    location = SerializerMethodField(read_only=True)
    in_crowd = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'location',
                  'first_name', 'last_name', 'in_crowd')
        depth = 1

    def get_email(self, obj):
        try:  # Return nothing if the settings don't exist for some reason
            view_email_level = UserPrivacySettings.objects.get(
                settings__user_id=obj.id)
        except:
            return ''

        requester_id = self.context.get('requester_id')

        if view_email_level == MIN_USER_PERMISSION:
            return obj.email
        elif view_email_level == MAX_USER_PERMISSION:
            if requester_id == obj.id:
                return obj.email
            return ''

        # If requester is in user's crowd return email
        try:
            CrowdRequest.objects.get(Q(sender=obj, receiver_id=requester_id, is_accepted=True) | Q(
                sender_id=requester_id, receiver=obj, is_accepted=True))
            return obj.email
        except:
            return ''

    def get_in_crowd(self, obj):
        requester_id = self.context.get('requester_id')
        try:
            CrowdRequest.objects.get(Q(sender=obj, receiver_id=requester_id, is_accepted=True)
                                     | Q(sender_id=requester_id, receiver=obj))
            return True
        except:
            return False

    def get_location(self, obj):
        return obj.profile.location


class UserDetailedGETSerializer(ModelSerializer):
    email = SerializerMethodField()
    profile = ProfileGETSerializer()
    skills = UserSkillSerializer(many=True)
    saved_tasks = SerializerMethodField()

    in_crowd = SerializerMethodField()
    show_crowd = SerializerMethodField()
    show_stats = SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'date_joined', 'last_login', 'profile', 'skills', 'saved_tasks',
                  'in_crowd', 'show_crowd', 'show_stats',)
        depth = 1

    def get_email(self, obj):
        view_email_level = UserPrivacySettings.objects.get(
            settings__user_id=obj.id).view_email_level

        requester_id = self.context.get('requester_id')

        if view_email_level == MIN_USER_PERMISSION:
            return obj.email
        elif view_email_level == MAX_USER_PERMISSION:
            if requester_id == obj.id:
                return obj.email
            return ''

        # if requester is in the user's crowd, get the email
        try:
            CrowdRequest.objects.get(Q(sender=obj, receiver_id=requester_id, is_accepted=True) | Q(
                sender_id=requester_id, receiver=obj, is_accepted=True))
            return obj.email
        except:
            return ''

    def get_show_crowd(self, obj):
        view_crowd_level = UserPrivacySettings.objects.get(
            settings__user_id=obj.id).view_crowd_level

        requester_id = self.context.get('requester_id')
        if requester_id == obj.id:
            return True

        if view_crowd_level == MIN_USER_PERMISSION:
            return True

        # If requester is in the user's crowd, return true
        try:
            CrowdRequest.objects.get(Q(sender=obj, receiver_id=requester_id, is_accepted=True) | Q(
                sender_id=requester_id, receiver=obj, is_accepted=True))
            return True
        except:
            return False

    def get_show_stats(self, obj):
        view_stats_level = UserPrivacySettings.objects.get(
            settings__user_id=obj.id).view_stats_level

        requester_id = self.context.get('requester_id')
        if requester_id == obj.id:
            return True

        if view_stats_level == MIN_USER_PERMISSION:
            return True

        # If requester is in the user's crowd, return true
        try:
            CrowdRequest.objects.get(Q(sender=obj, receiver_id=requester_id, is_accepted=True) | Q(
                sender_id=requester_id, receiver=obj, is_accepted=True))
            return True
        except:
            return False

    def get_in_crowd(self, obj):
        requester_id = self.context.get('requester_id')
        try:
            CrowdRequest.objects.get(Q(sender=obj, receiver_id=requester_id, is_accepted=True)
                                     | Q(sender_id=requester_id, receiver=obj))
            return True
        except:
            return False

    def get_saved_tasks(self, obj):
        try:
            requester_id = self.context.get('requester_id')
            if not obj.id == requester_id:
                raise ValidationError(
                    'requester must be the user to get saved tasks')
        except:
            return []
        return UserTaskGETSerializer(obj.saved_tasks, many=True).data


class UserPOSTSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password',
                  'email', 'first_name', 'last_name')

    def create(self, validated_data):
        # Check if username fits requirements
        username = validated_data['username']
        if not re.fullmatch(r'([a-zA-Z0-9]{3,20}$)', username):
            raise ValidationError('username does not fit requirements')

        try:
            # Check if username is already taken
            User.objects.get(username=username)
            raise ValidationError('username is taken')
        except ValidationError:
            raise
        except:
            pass

        # Check if email is valid
        email = validated_data['email']
        if not re.fullmatch(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', email):
            raise ValidationError('email is invalid')

        try:
            # Check if email is already taken
            User.objects.get(email=validated_data['email'])
            raise ValidationError('email is taken')
        except ValidationError:
            raise
        except:
            pass

        # Check if password fits regex
        password = validated_data['password']
        if not re.fullmatch(r"(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[-!@$%^&*()_+|~=`{}\[\]:;'<>?,.\/\\])[A-Za-z0-9-!@$%^&*()_+|~=`{}\[\]:;'<>?,.\/\\]{8,}", password):
            raise ValidationError('password does not fit requirements')

        return User.objects.create(
            username=username,
            password=make_password(password),
            email=email,
            last_login=timezone.now(),
            is_active=False)


class UserPATCHSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'last_login')


class ProfilePATCHSerializer(ModelSerializer):
    user = UserPOSTSerializer()

    class Meta:
        model = Profile
        fields = ('id', 'user', 'bio', 'location', 'birth_date', 'image',
                  'created', 'last_updated')
        depth = 1
