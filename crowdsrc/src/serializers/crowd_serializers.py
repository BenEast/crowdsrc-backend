# Crowdsrc imports
from crowdsrc.src.models import CrowdRequest
from crowdsrc.src.serializers import UserListGETSerializer

# Django imports
from rest_framework.serializers import ModelSerializer


class CrowdRequestPOSTSerializer(ModelSerializer):
    class Meta:
        model = CrowdRequest
        fields = '__all__'


class CrowdRequestReceivedSerializer(ModelSerializer):
    sender = UserListGETSerializer()

    class Meta:
        model = CrowdRequest
        fields = ('sender', 'is_viewed')
