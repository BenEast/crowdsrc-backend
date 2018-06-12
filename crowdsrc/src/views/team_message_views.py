# Crowdsrc imports
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from crowdsrc.settings import CREATE, UPDATE, DELETE
from .views import *

# Django imports
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.response import Response


class TeamMessageViewSet(ModelViewSet):
    queryset = TeamMessage.objects.all()
    serializer_class = TeamMessageGETSerializer

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return TeamMessagePOSTSerializer
        else:
            return self.serializer_class

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        serializer = TeamMessagePOSTSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            log_event(request, None, self.queryset.get(
                id=serializer.data.get('id')), CREATE)

            return Response(serializer.data, status=HTTP_201_CREATED,
                            headers=self.get_success_headers(serializer.data))

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        try:
            instance = self.queryset.get(id=pk)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Determine if requesting user created the message prior to update
        if not instance.user_id == request.user.id:
            return Response(status=HTTP_401_UNAUTHORIZED)

        request.data['last_updated'] = timezone.now()
        serializer = self.serializer_class(
            self.queryset.get(id=pk), data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            log_event(request, instance, self.queryset.get(id=pk), UPDATE)

            return Response(serializer.data, status=HTTP_200_OK)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            instance = TeamMessage.objects.get(id=pk)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Determine if requesting user is message creator
        # or project creator prior to delete
        if instance.user_id != request.user.id or instance.project.user_id != request.user.id:
            return Response(status=HTTP_401_UNAUTHORIZED)

        log_event(request, instance, None, DELETE)

        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class TeamMessageReplyCreateView(CreateAPIView):
    queryset = TeamMessageReply.objects.all()
    serializer_class = TeamMessageReplyPOSTSerializer

    def create(self, request, message_id=None, *args, **kwargs):
        request.data['user'] = request.user.id
        request.data['message'] = message_id

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            instance = self.queryset.get(id=serializer.data.get('id'))

            log_event(request, None, instance, CREATE)

            return Response(TeamMessageReplyGETSerializer(instance).data,
                            status=HTTP_201_CREATED)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class TeamMessageReplyRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = TeamMessageReply.objects.all()
    serializer_class = TeamMessageReplyPOSTSerializer

    def partial_update(self, request, message_id=None, reply_id=None, *args, **kwargs):
        try:
            instance = self.queryset.get(id=reply_id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        if instance.user_id != request.user.id:
            return Response(status=HTTP_401_UNAUTHORIZED)

        request.data['last_updated'] = timezone.now()
        serializer = self.serializer_class(
            self.queryset.get(id=reply_id), data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            log_event(request, instance,
                      self.queryset.get(id=reply_id), UPDATE)

            return Response(TeamMessageReplyGETSerializer(self.queryset.get(id=reply_id)).data,
                            status=HTTP_201_CREATED)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def destroy(self, request, message_id=None, reply_id=None, *args, **kwargs):
        try:
            instance = self.queryset.get(id=reply_id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Determine if requesting user is message creator
        # or project creator prior to delete
        if instance.user_id != request.user.id or instance.message.project.user_id != request.user.id:
            return Response(status=HTTP_401_UNAUTHORIZED)

        log_event(request, instance, None, DELETE)

        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)
