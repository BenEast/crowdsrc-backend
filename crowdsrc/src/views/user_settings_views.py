

# Crowdsrc imports
from crowdsrc.settings import CREATE, DELETE, UPDATE, USER_PERMISSION_ROLES
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from .views import *

# Django imports
from django.db.models import Q
from rest_framework.generics import GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST


class BlockedUserView(GenericAPIView, CreateModelMixin, DestroyModelMixin):
    queryset = BlockedUser.objects.all()
    serializer_class = BlockedUserPOSTSerializer

    def post(self, request, username=None, *args, **kwargs):
        try:
            target = User.objects.get(username=username)
        except:
            return Response('invalid username', status=HTTP_400_BAD_REQUEST)

        # Create the block object
        serializer = self.serializer_class(
            data={'source': request.user.id, 'target': target.id})
        if serializer.is_valid():
            serializer.save()

            instance = self.queryset.get(id=serializer.data.get('id'))

            log_event(request, None, instance, CREATE)

            # Delete any CrowdRequests between the users
            try:
                crowd_request = CrowdRequest.objects.get(Q(sender__username=username, receiver_id=request.user.id) | Q(
                    sender_id=request.user.id, receiver__username=username))
                log_event(request, crowd_request, None, DELETE)
                crowd_request.delete()
            except:
                pass

            return Response(BlockedUserGETSerializer(instance).data, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, username=None, *args, **kwargs):
        try:
            instance = self.queryset.get(
                source=request.user.id, target__username=username)
        except:
            return Response('invalid username', status=HTTP_400_BAD_REQUEST)

        log_event(request, instance, None, DELETE)

        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class UserSettingsRetrieveView(RetrieveAPIView):
    queryset = UserSettings.objects.all()
    serializer_class = UserSettingsSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.queryset.get(user_id=request.user.id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(
            instance, context={'requester_id': request.user.id})

        return Response(serializer.data, status=HTTP_200_OK)


class UserPrivacySettingsUpdateView(UpdateAPIView):
    queryset = UserPrivacySettings.objects.all()
    serializer_class = UserPrivacySettingsPOSTSerializer

    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.queryset.get(settings__user_id=request.user.id)

            # Try to transform user data strings to database int values
            if request.query_params.get('section') == 'view':
                request.data['view_activity_level'] = USER_PERMISSION_ROLES.index(
                    request.data['view_activity_level'])

                request.data['view_age_level'] = USER_PERMISSION_ROLES.index(
                    request.data['view_age_level'])

                request.data['view_email_level'] = USER_PERMISSION_ROLES.index(
                    request.data['view_email_level'])

                request.data['view_crowd_level'] = USER_PERMISSION_ROLES.index(
                    request.data['view_crowd_level'])

                request.data['view_stats_level'] = USER_PERMISSION_ROLES.index(
                    request.data['view_stats_level'])
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(self.queryset.get(settings__user_id=request.user.id),
                                           data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            log_event(request, instance, self.queryset.get(
                settings__user_id=request.user.id), UPDATE)

            return Response(status=HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class UserPreferencesUpdateView(UpdateAPIView):
    queryset = UserPreferences.objects.all()
    serializer_class = UserPreferencesPOSTSerializer

    def partial_update(self, request):
        try:
            instance = self.queryset.get(settings__user_id=request.user.id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        if request.query_params.get('section') == 'preferences':
            # Update skill preferences
            skill_preferences = request.data.pop('skill_preferences')
            for entry in skill_preferences:
                try:
                    skill = UserSkill.objects.get(
                        user_id=request.user.id, skill__name=entry.get('name'))
                    skill.is_preferred = entry['preferred']

                    log_event(request, UserSkill.objects.get(
                        user_id=request.user.id, skill__name=entry.get('name')), skill, UPDATE)

                    skill.save()
                except:
                    pass
            return Response(status=HTTP_204_NO_CONTENT)

        serializer = self.serializer_class(self.queryset.get(settings__user_id=request.user.id),
                                           data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            log_event(request, instance, self.queryset.get(
                settings__user_id=request.user.id), UPDATE)

            return Response(status=HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
