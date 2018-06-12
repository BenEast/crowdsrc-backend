from ntpath import basename
from os.path import getsize

# Crowdsrc imports
from crowdsrc.settings import TASK_STATUS_NAMES
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from crowdsrc.src.views import *

# Django imports
from rest_framework.serializers import ModelSerializer


class ReviewSuggestionSerializer(ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = ('id')


class ReviewPOSTSerializer(ModelSerializer):
    class Meta:
        model = SubmissionReview
        fields = ('id', 'submission', 'reviewer', 'created', 'rating')


# class ReviewGETSerializer(ModelSerializer):
#     class Meta:
#         model = SubmissionReview
#         fields = ('id', 'submission', 'reviewer', 'created', 'rating')


class SkillReviewPOSTSerializer(ModelSerializer):
    class Meta:
        model = SubmissionSkillReview
        fields = ('id', 'review', 'skill', 'rating')


class ReviewSubmissionSerializer(ModelSerializer):
    files = SerializerMethodField()

    class Meta:
        model = TaskSubmission
        fields = ('id', 'is_accepted', 'last_updated', 'files')

    def get_files(self, obj):
        # LATER check if requester has skill level to review
        files = []
        for submission in obj.files.all():
            files.append({'id': submission.id,
                          'filename': basename(submission.file.url),
                          'size': getsize(submission.file.url.replace('%3A', ':'))})
        return files


class ReviewTaskSerializer(ModelSerializer):
    status = SerializerMethodField(read_only=True)
    skills = TaskSkillSerializer(many=True)

    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'created',
                  'last_updated', 'status', 'skills')

    def get_status(self, obj):
        return TASK_STATUS_NAMES[obj.status_level]
