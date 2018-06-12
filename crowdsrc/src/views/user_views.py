import base64
import os
from shutil import move
from ntpath import basename
from PIL import Image

# Crowdsrc imports
from crowdsrc.src.filters import UserSearchFilter
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from crowdsrc.settings import CREATE, DELETE, USER_IMAGE_ROOT
from .views import *

# Django imports
from django.db.models import Q
from django.core.files import File
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.response import Response
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import IsAuthenticated


class NotificationListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=request.user.id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        return Response(self.serializer_class(user).data, status=HTTP_200_OK)


class UserImageRetrieveUpdateView(RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = UserImageSerializer

    def get_file_size(self, base64: str):
        return (len(base64) * 3) / 4 - base64.count('=', -2)

    def make_thumbnails(self, image_path):
        sizes = {'sm': (64, 64), 'md': (128, 128)}

        image_dir = os.path.dirname(image_path)
        filename = basename(image_path).split('.')[0]

        for key in sizes.keys():
            image = Image.open(image_path)
            image.thumbnail(sizes.get(key))
            image.save(os.path.join(image_dir, filename + '-' + key + '.png'))

    def move_old_image(self, old_image_path):
        filename = basename(old_image_path)
        dir_name = os.path.dirname(old_image_path)
        old_dir = os.path.join(dir_name, 'old')

        if not os.path.exists(old_dir):
            os.makedirs(old_dir)

        try:
            old_dir = os.path.join(old_dir, filename)
            move(old_image_path, old_dir)
        except:
            pass

        # Delete old thumbnails
        filename, ext = filename.split('.')
        try:
            os.remove(os.path.join(dir_name, filename + '-sm.' + ext))
            os.remove(os.path.join(dir_name, filename + '-md.' + ext))
        except:
            pass

    def partial_update(self, request, username=None):
        try:
            profile = self.queryset.get(user__username=username)

            if not profile.user_id == request.user.id:
                raise ValueError('Incorrect credentials')
        except ValueError as e:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        old_image_path = str(profile.image).replace('\\', '/')

        # Check file size prior to upload
        if self.get_file_size(request.data.get('image')) > 5242880:
            return Response('File size must be less than 5MB', status=HTTP_400_BAD_REQUEST)

        serializer = UserImageSerializer(
            self.queryset.get(user__username=username), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            log_event(request, profile, self.queryset.get(
                user__username=username), UPDATE, extra={'note': 'changed image'})

            if not old_image_path == os.path.join(USER_IMAGE_ROOT, 'default.png').replace('\\', '/'):
                self.move_old_image(old_image_path)

            self.make_thumbnails(str(
                self.queryset.get(user__username=username).image
            ))

            return Response(status=HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def retrieve(self, request, username=None):
        try:
            image_path = str(self.queryset.get(user__username=username).image)
            size = self.request.query_params.get('size', None)

            # Get a thumbnail if size query param is valid
            if size in ('sm', 'md'):
                image_path, ext = image_path.split('.')
                image_path = image_path + '-' + size + '.' + ext

            with open(image_path, 'rb') as file:
                data = base64.b64encode(file.read()).decode('utf-8')
            return Response('data:image/png;base64,' + data, status=HTTP_200_OK)
        except Exception as e:
            return Response(status=HTTP_400_BAD_REQUEST)


class UserListView(ListAPIView):
    queryset = User.objects.all().only('id', 'username')
    serializer_class = UserListGETSerializer

    def list(self, request):
        # Filter out users that are blocking the requester
        if not request.user.id == None:
            blocked = BlockedUser.objects.filter(target_id=request.user.id)
            queryset = queryset.exclude(id__in=blocked.values('source_id'))

        serializer = self.serializer_class(self.queryset, many=True,
                                           context={'requester_id': request.user.id})

        return Response(serializer.data, status=HTTP_200_OK)


class UserDetailedView(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailedGETSerializer

    def get_serializer_class(self):
        if self.request.method is 'PATCH':
            return UserPATCHSerializer
        else:
            return self.serializer_class

    def retrieve(self, request, username=None):
        if not request.user.id == None:
            # Check if the requesting user is blocked by this user
            try:
                BlockedUser.objects.get(
                    source__username=username, target_id=request.user.id)
                return Response('blocked', status=HTTP_401_UNAUTHORIZED)
            except:
                pass

        user = User.objects.get(username=username)
        serializer = self.serializer_class(
            user, context={'requester_id': request.user.id})

        return Response(serializer.data, status=HTTP_200_OK)

    def partial_update(self, request, username=None):
        user = User.objects.get(username=username)
        # Check request auth token before performing action
        if not user.id == request.user.id:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Filter out empty values
        profile_data = request.data.pop('profile')
        if not profile_data.get('birth_date'):
            profile_data['birth_date'] = None

        # Update profile fields
        profile = Profile.objects.get(user_id=user.id)
        profile_serializer = ProfilePATCHSerializer(
            Profile.objects.get(user_id=user.id), data=profile_data, partial=True)

        if profile_serializer.is_valid():
            profile_serializer.save()

            log_event(request, profile, Profile.objects.get(
                user_id=user.id), UPDATE)
        else:
            return Response(profile_serializer.errors, status=HTTP_400_BAD_REQUEST)

        # Update user fields
        # Restrict to only first_name, last_name to prevent manipulation
        # of other data fields
        user_serializer = UserPATCHSerializer(
            User.objects.get(username=username),
            data={'first_name': request.data.pop('first_name'),
                  'last_name': request.data.pop('last_name')}, partial=True)

        if user_serializer.is_valid():
            user_serializer.save()

            log_event(request, user, User.objects.get(
                username=username), UPDATE)
        else:
            return Response(user_serializer.errors, status=HTTP_400_BAD_REQUEST)

        return Response(self.serializer_class(
            User.objects.get(username=username), context={'requester_id': request.user.id}
        ).data, status=HTTP_200_OK)


class UserListView(ListAPIView):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSearchSerializer
    filter_backends = (UserSearchFilter,)


class DeleteUserView(GenericAPIView, DestroyModelMixin):
    queryset = User.objects.all()
    serializer_class = UserListGETSerializer

    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=request.user.id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Check if password is correct
        if not user.check_password(request.data.get('password')):
            return Response(status=HTTP_401_UNAUTHORIZED)

        # Save feedback in auditlog comment
        log_event(request, user, None, DELETE, extra={
                  'feedback': request.data.get('feedback')})

        user.delete()
        return Response(status=HTTP_204_NO_CONTENT)
