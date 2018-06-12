# Crowdsrc imports
from crowdsrc.src.models import TeamMessage, TeamMessageReply
from .user_serializers import UserListGETSerializer

# Django imports
from rest_framework import serializers


class TeamMessageReplyGETSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()

    class Meta:
        model = TeamMessageReply
        fields = ('id', 'user', 'body', 'last_updated')


class TeamMessageReplyPOSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMessageReply
        fields = ('id', 'message', 'user', 'body', 'created', 'last_updated')


class TeamMessageGETSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()
    replies = TeamMessageReplyGETSerializer(many=True)

    class Meta:
        model = TeamMessage
        fields = ('id', 'user', 'body', 'created', 'last_updated', 'replies')


class TeamMessagePOSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMessage
        fields = ('id', 'project', 'user', 'body', 'created', 'last_updated')
