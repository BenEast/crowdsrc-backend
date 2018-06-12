# Crowdsrc imports
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from crowdsrc.settings import USER_PERMISSION_ROLES

# Django imports
from rest_framework.serializers import ModelSerializer, SerializerMethodField


class BlockedUserGETSerializer(ModelSerializer):
    target = UserListGETSerializer()

    class Meta:
        model = BlockedUser
        fields = ('id', 'target', 'created')


class BlockedUserPOSTSerializer(ModelSerializer):
    class Meta:
        model = BlockedUser
        fields = ('id', 'source', 'target', 'created')


class UserPrivacySettingsGETSerializer(ModelSerializer):
    blocked_users = SerializerMethodField(read_only=True)
    view_activity_level = SerializerMethodField(read_only=True)
    view_age_level = SerializerMethodField(read_only=True)
    view_email_level = SerializerMethodField(read_only=True)
    view_crowd_level = SerializerMethodField(read_only=True)
    view_stats_level = SerializerMethodField(read_only=True)

    class Meta:
        model = UserPrivacySettings
        fields = ('blocked_users', 'allow_email_search', 'allow_loc_search',
                  'allow_name_search', 'allow_username_search', 'view_activity_level',
                  'view_age_level', 'view_email_level', 'view_crowd_level', 'view_stats_level')

    def get_blocked_users(self, obj):
        serializer = BlockedUserGETSerializer(
            BlockedUser.objects.filter(source=obj.settings.user), many=True)
        return serializer.data

    def get_view_activity_level(self, obj):
        return USER_PERMISSION_ROLES[obj.view_activity_level]

    def get_view_age_level(self, obj):
        return USER_PERMISSION_ROLES[obj.view_age_level]

    def get_view_email_level(self, obj):
        return USER_PERMISSION_ROLES[obj.view_email_level]

    def get_view_crowd_level(self, obj):
        return USER_PERMISSION_ROLES[obj.view_crowd_level]

    def get_view_stats_level(self, obj):
        return USER_PERMISSION_ROLES[obj.view_stats_level]


class UserPrivacySettingsPOSTSerializer(ModelSerializer):
    class Meta:
        model = UserPrivacySettings
        fields = '__all__'


class UserPreferencesGETSerializer(ModelSerializer):
    skill_preferences = SerializerMethodField(read_only=True)

    class Meta:
        model = UserPreferences
        fields = ('notify_crowd_request_accept', 'notify_message_replies', 'notify_project_messages',
                  'notify_project_submissions', 'notify_saved_task_status', 'notify_submission_status',
                  'skill_preferences',)

    def get_skill_preferences(self, obj):
        skills = UserSkill.objects.filter(user_id=obj.settings.user_id)
        return UserSkillSerializer(skills, many=True, context=self.context).data


class UserPreferencesPOSTSerializer(ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = '__all__'


class UserSettingsSerializer(ModelSerializer):
    privacy = UserPrivacySettingsGETSerializer()
    preferences = UserPreferencesGETSerializer()

    class Meta:
        model = UserSettings
        fields = ('privacy', 'preferences')
