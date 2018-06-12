import base64
from mimetypes import guess_extension
import uuid

# Crowdsrc imports
from crowdsrc.settings import *
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from .views import *

# Django imports
from django.core.files.base import ContentFile
from rest_framework.generics import CreateAPIView, RetrieveDestroyAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.response import Response


def get_extension(header: str) -> str:
    # Determine file extension from base64 header
    mime = header.split(':')[1]
    if mime == 'text/plain':
        return '.txt'
    extension = guess_extension(mime)

    if not extension:
        return '.txt'

    return extension


def get_file_size(base64: str) -> int:
    return (len(base64) * 3) / 4 - base64.count('=', -2)


def create_submission_files(request, submission_id):
    submission_data = request.data.get('submission')
    if not submission_data or not type(submission_data) == list:
        return

    for entry in submission_data:
        file_data = entry.get('data')

        if ';base64,' in file_data:
            header, data = file_data.split(';base64,')
        else:
            continue

        # If the file size is > 5 MB don't save the file and continue
        if get_file_size(data) > 5242880:
            continue

        # Try to get the filename
        # Create a new filename if one wasn't provided
        file_name = entry.get('filename',
                              str(uuid.uuid4())[:12] + get_extension(header))

        content = ContentFile(base64.b64decode(data), name=file_name)

        file_serializer = SubmissionFilePOSTSerializer(
            data={'submission': submission_id, 'file': content})
        if file_serializer.is_valid():
            file_serializer.save()

            log_event(request, None, SubmissionFile.objects.get(
                id=file_serializer.data.get('id')), CREATE)


def move_old_file(old_file_path: str):
    file_extension = basename(old_file_path).split('.')[1]
    old_dir = os.path.dirname(old_file_path) + '/old'

    if not os.path.exists(old_dir):
        os.makedirs(old_dir)

    try:
        old_dir = (old_dir + '/' + str(uuid.uuid4())[:12]
                   + '.' + file_extension)
        os.rename(old_file_path, old_dir)
    except:
        pass


class TaskSubmissionListCreateView(CreateAPIView):
    queryset = TaskSubmission.objects.all()
    serializer_class = TaskSubmissionGETSerializer

    def get_serializer_context(self):
        return {'requester_id': self.request.user.id}

    def create(self, request, task_id=None):
        try:
            # Check if the task is complete before continuing
            task = Task.objects.get(id=task_id)
            if task.status_level == MAX_TASK_STATUS:
                raise ValueError('Task is complete')
        except:
            return Response('Task is already complete', status=HTTP_400_BAD_REQUEST)

        if not len(request.data.get('submission')):
            return Response('No files were submitted', status=HTTP_400_BAD_REQUEST)

        # Create the TaskSubmission object
        serializer = TaskSubmissionPOSTSerializer(
            data={'task': task_id, 'user': request.user.id})

        if serializer.is_valid():
            serializer.save()

            # Create SubmissionFile objects for each file submitted
            create_submission_files(request, serializer.data.get('id'))

            # If no other submissions, update task status to pending approval
            if len(self.queryset.filter(task_id=task_id).values_list('id', flat=True)) == 1:
                task = Task.objects.get(id=task_id)
                task.status_level = 1

                log_event(request, Task.objects.get(id=task_id), task, UPDATE)

                task.save()

            instance = self.queryset.get(id=serializer.data.get('id'))

            log_event(request, None, instance, CREATE)

            # Retrieve all data and return
            output_serializer = TaskSubmissionGETSerializer(
                instance, context=self.get_serializer_context())

            return Response(output_serializer.data, status=HTTP_201_CREATED)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class TaskSubmissionRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = TaskSubmission.objects.all()
    serializer_class = TaskSubmissionGETSerializer

    def get_serializer_context(self):
        return {'requester_id': self.request.user.id}

    def destroy(self, request, task_id=None, submission_id=None):
        # Check if requester is the posting user or project creator prior to delete
        try:
            instance = self.queryset.get(id=submission_id)

            if request.user.id != instance.user_id and request.user.id != instance.project.user_id:
                raise ValueError("You don't have permission to do that!")

            # Check if instance is_accepted
            if instance.is_accepted:
                raise ValueError('Cannot delete accepted submission')
        except ValueError:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Move all files related to the submission into the /old subfolder
        for submission_file in list(instance.files.values_list('file', flat=True)):
            move_old_file(str(submission_file))

        log_event(request, instance, None, DELETE)

        instance.delete()

        # Set task status to incomplete if no other submissions
        if not len(self.queryset.filter(task_id=task_id).values_list('id', flat=True)):
            task = Task.objects.get(id=task_id)
            task.status_level = MIN_TASK_STATUS

            log_event(request, Task.objects.get(id=task_id), task, UPDATE)

            task.save()

        return Response(status=HTTP_204_NO_CONTENT)

    def partial_update(self, request, task_id=None, submission_id=None, *args, **kwargs):
        # Check if requester is project creator or submission creator
        try:
            instance = self.queryset.get(id=submission_id)
            project_creator = instance.task.project.user_id

            if instance.user_id != request.user.id and project_creator != request.user.id:
                raise ValueError('Must be project creator to update this')

        except ValueError:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        is_accepted = request.data.get('is_accepted')

        # If requester is project creator, try to update the is_accepted value
        # and no other submissions have been accepted for this task, accept the submission
        if request.user.id == project_creator and is_accepted != None:
            accepted_values = list(self.queryset.filter(
                task_id=task_id).values_list('is_accepted', flat=True))

            if (is_accepted == False) or is_accepted and not True in accepted_values:
                instance.is_accepted = is_accepted
                instance.accepted_date = timezone.now()

                log_event(request, self.queryset.get(
                    id=submission_id), instance, UPDATE)

                instance.save()

                # If is_accepted = True, make task completed
                # Else make the task pending approval
                task = Task.objects.get(id=task_id)
                if is_accepted:
                    task.status_level = MAX_TASK_STATUS
                else:
                    task.status_level = 1

                log_event(request, Task.objects.get(id=task_id), task, UPDATE)

                task.save()

        # Check if task is not complete before adding more files
        task = Task.objects.get(id=task_id)
        if task.status_level != MAX_TASK_STATUS and request.user.id == instance.user_id:
            # Try to create SubmissionFile objects for each file submitted
            create_submission_files(request, submission_id)
            instance.last_updated = timezone.now()
            instance.save()

        return Response(TaskSubmissionGETSerializer(instance, context=self.get_serializer_context()).data,
                        status=HTTP_200_OK)

    def retrieve(self, request, task_id=None, submission_id=None):
        # This will need to be updated to check user skill or qualification
        # level once we gain momentum
        task = Task.objects.get(id=task_id)
        task_serializer = ReviewTaskSerializer(task)

        submission = self.queryset.get(id=submission_id)
        submission_serializer = ReviewSubmissionSerializer(submission)

        return Response({'task': task_serializer.data,
                         'submission': submission_serializer.data}, status=HTTP_200_OK)


class SubmissionFileDataView(RetrieveDestroyAPIView):
    queryset = SubmissionFile.objects.all()
    serializer_class = SubmissionFileDataSerializer

    def retrieve(self, request, id=None, *args, **kwargs):
        try:
            instance = self.queryset.get(id=id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        serializer = SubmissionFileDataSerializer(instance)
        return Response(serializer.data, status=HTTP_200_OK)

    def destroy(self, request, id=None, *args, **kwargs):
        try:
            instance = self.queryset.get(id=id)
            # If submission is_accepted, we can't make any changes
            if instance.submission.is_accepted:
                raise ValueError("Can't edit after submission is accepted")

            # If task is complete, we can't delete single files,
            # only the entire submission can be removed.
            task = Task.objects.get(id=instance.submission.task_id)
            if task.status_level == MAX_TASK_STATUS:
                raise ValueError('Task has already been completed')

            # Check if requester submitted the file before delete
            if instance.submission.user_id != request.user.id:
                raise ValueError("You don't have permission to delete this")
        except ValueError:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        file_count = self.queryset.filter(
            submission_id=instance.submission_id).distinct().count()

        # Move the file to the /old subdirectory
        move_old_file(str(instance.file))

        submission = TaskSubmission.objects.get(id=instance.submission_id)

        # If there is more than 1 file for this submission, delete just
        # this file
        if file_count > 1:
            # Update the last updated value for the submission
            submission.last_updated = timezone.now()
            submission.save()

            log_event(request, instance, None, DELETE)

            instance.delete()
            submission_deleted = False
        # Else delete the whole task submission
        else:
            task_id = submission.task_id

            log_event(request, submission, None, DELETE)

            submission.delete()
            submission_deleted = True

            # If there are no other submissions for the task, set the
            # status to incomplete
            if not len(TaskSubmission.objects.filter(task_id=task_id).values_list('id', flat=True)):
                task = Task.objects.get(id=task_id)
                task.status_level = MIN_TASK_STATUS

                log_event(request, Task.objects.get(id=task_id), task, UPDATE)

                task.save()

        return Response({'submission_deleted': submission_deleted}, status=HTTP_200_OK)
