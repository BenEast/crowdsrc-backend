# Crowdsrc imports
from crowdsrc.src.models import Task, UserTask
from crowdsrc.settings import TASK_STATUS_NAMES
from .skill_serializers import TaskSkillSerializer
from .task_submission_serializers import TaskSubmissionGETSerializer

# Django imports
from rest_framework.serializers import ModelSerializer, SerializerMethodField


class TaskGETSerializer(ModelSerializer):
    status = SerializerMethodField(read_only=True)
    submissions = TaskSubmissionGETSerializer(many=True)
    skills = TaskSkillSerializer(many=True)
    is_saved = SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'status', 'created',
                  'last_updated', 'skills', 'submissions', 'is_saved')

    def get_status(self, obj):
        return TASK_STATUS_NAMES[obj.status_level]

    def get_is_saved(self, obj):
        try:
            requester_id = self.context.get('requester_id')
            UserTask.objects.get(user_id=requester_id, task_id=obj.id)
            return True
        except:
            return False


class TaskPOSTSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'project', 'title', 'description', 'last_updated')


class TaskSuggestionSerializer(ModelSerializer):
    status = SerializerMethodField(read_only=True)
    shared_skills = SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = ('project_id', 'title', 'description', 'status',
                  'last_updated', 'shared_skills')

    def get_status(self, obj):
        return TASK_STATUS_NAMES[obj.status_level]

    def get_shared_skills(self, obj):
        user_skills = self.context.get('user_skills')
        return TaskSkillSerializer(obj.skills.filter(skill__in=user_skills), many=True).data[:3]
