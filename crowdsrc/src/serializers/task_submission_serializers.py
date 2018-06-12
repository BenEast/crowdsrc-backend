import base64
from mimetypes import guess_type
from ntpath import basename
from os.path import getsize

# Crowdsrc imports
from crowdsrc.src.models import TaskSubmission, SubmissionFile

# Django imports
from rest_framework.serializers import FileField, ModelSerializer, SerializerMethodField


class TaskSubmissionGETSerializer(ModelSerializer):
    files = SerializerMethodField()

    class Meta:
        model = TaskSubmission
        fields = ('id', 'user_id', 'is_accepted', 'last_updated', 'files')

    def get_files(self, obj):
        # Check if requester is project creator
        try:
            if (self.context.get('requester_id') != obj.task.project.user_id
                    and self.context.get('requester_id') != obj.user_id):
                raise ValueError(
                    'Only project or submission creator can view files')
        except:
            return []

        files = []
        for submission in obj.files.all():
            files.append({'id': submission.id,
                          'filename': basename(submission.file.url),
                          'size': getsize(submission.file.url.replace('%3A', ':'))})
        return files


class SubmissionFileDataSerializer(ModelSerializer):
    file = SerializerMethodField()

    class Meta:
        model = SubmissionFile
        fields = ('file',)

    def get_mime_type(self, file_path) -> str:
        file_type, _ = guess_type(file_path)
        if not file_type:
            return ''
        return file_type

    def get_file(self, obj):
        file_path = obj.file.url.replace('%3A', ':')
        with open(file_path, 'rb') as file:
            data = base64.b64encode(file.read()).decode('utf-8')

        return 'data:' + self.get_mime_type(file_path) + ';base64,' + data


class SubmissionFilePOSTSerializer(ModelSerializer):
    file = FileField()

    class Meta:
        model = SubmissionFile
        fields = ('id', 'submission', 'file')


class TaskSubmissionPOSTSerializer(ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = ('id', 'task', 'user', 'is_accepted')
