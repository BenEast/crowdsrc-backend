from crowdsrc.src.models import Project, Task, User
from crowdsrc.src.serializers import ProjectDetailedGETSerializer, TaskGETSerializer, UserDetailedGETSerializer

from django.db.models import Model
from rest_framework.serializers import ModelSerializer


class GlobalSearchSerializer(ModelSerializer):
    class Meta:
        model = Model

    def to_native(self, obj):
        if isinstance(obj, Project):
            serializer = ProjectDetailedGETSerializer(obj)
        elif isinstance(obj, Task):
            serializer = TaskGETSerializer(obj)
        elif isinstance(obj, User):
            serializer = UserDetailedGETSerializer(obj)
        else:
            raise Exception('Invalid global search instance type!')
        return serializer.data
