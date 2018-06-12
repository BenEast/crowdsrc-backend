# Crowdsrc imports
from crowdsrc.settings import CREATE, DELETE, UPDATE
from crowdsrc.src.models import CrowdRequest, User
from crowdsrc.src.serializers import *
from crowdsrc.src.views import log_event

# Django imports
from django.db.models import Q
from rest_framework.generics import ListAPIView, UpdateAPIView, GenericAPIView
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from rest_framework.response import Response


class UserCrowdListView(ListAPIView):
    queryset = CrowdRequest.objects.all()
    serializer_class = UserListGETSerializer

    def get_other_users(self, user, queryset):
        senders = queryset.exclude(
            Q(sender_id=user.id)).values_list('sender_id')
        receivers = queryset.exclude(
            Q(receiver_id=user.id)).values_list('receiver_id')

        users = User.objects.filter(Q(id__in=senders) | Q(id__in=receivers))

        return self.serializer_class(users, many=True,
                                     context={'requester_id': self.request.user.id}).data

    def list(self, request, username=None, *args, **kwargs):
        try:
            user = User.objects.get(username=username)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(Q(sender__username=username)
                                        | Q(receiver__username=username))

        crowd = self.get_other_users(user, queryset.filter(is_accepted=True))

        # Only get pending requests if the requester is getting their own crowd
        if user.id == request.user.id:
            pending = self.get_other_users(
                user, self.queryset.filter(sender_id=request.user.id).exclude(is_accepted=True))

            received = self.queryset.filter(receiver_id=request.user.id).exclude(
                Q(is_accepted=True) | Q(is_rejected=True))
            received = CrowdRequestReceivedSerializer(received, many=True).data
        else:
            pending = []
            received = []

        return Response({'crowd': crowd, 'pending': pending, 'received': received}, status=HTTP_200_OK)


class CrowdRequestCreateDestroyView(GenericAPIView, CreateModelMixin, DestroyModelMixin):
    queryset = CrowdRequest.objects.all()
    serializer_class = CrowdRequestPOSTSerializer

    def post(self, request, username=None, *args, **kwargs):
        try:
            receiver = User.objects.get(username=username)

            if receiver.id == request.user.id:
                return Response(status=HTTP_400_BAD_REQUEST)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(
            data={'sender': request.user.id, 'receiver': receiver.id})

        if serializer.is_valid():
            serializer.save()
            instance = self.queryset.get(id=serializer.data.get('id'))

            log_event(request, None, instance, CREATE)

            return Response(serializer.data, status=HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, username=None, *args, **kwargs):
        try:
            instance = self.queryset.get(Q(sender_id=request.user.id, receiver__username=username)
                                         | Q(sender__username=username, receiver_id=request.user.id))
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        log_event(request, instance, None, DELETE)

        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class CrowdRequestUpdateView(UpdateAPIView):
    queryset = CrowdRequest.objects.all()
    serializer_class = CrowdRequestPOSTSerializer

    def partial_update(self, request, sender_username=None, *args, **kwargs):
        try:
            instance = self.queryset.get(
                sender__username=sender_username, receiver_id=request.user.id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Only update certain fields to be safe
        if request.data.get('is_accepted'):
            instance.is_accepted = True
            instance.responded = timezone.now()
        elif request.data.get('is_rejected'):
            instance.is_rejected = True
            instance.responded = timezone.now()

        instance.is_viewed = True

        log_event(request, self.queryset.get(
            sender__username=sender_username, receiver_id=request.user.id), instance, UPDATE)

        instance.save()

        if request.data.get('is_accepted'):
            return Response(UserListGETSerializer(User.objects.get(username=sender_username)).data, status=HTTP_200_OK)
        else:
            return Response(status=HTTP_204_NO_CONTENT)