# Crowdsrc imports
from crowdsrc.settings import *
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from .views import *

# Django imports
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.response import Response
from rest_framework.filters import SearchFilter


class UserTaskView(GenericAPIView, CreateModelMixin, DestroyModelMixin):
    queryset = UserTask.objects.all()
    serializer_class = UserTaskPOSTSerializer

    def post(self, request, task_id=None, *args, **kwargs):
        # Get requester id and verify that task_id is valid
        try:
            Task.objects.get(id=task_id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Create the instance
        serializer = self.serializer_class(
            data={'user': request.user.id, 'task': task_id})

        if serializer.is_valid():
            serializer.save()

            log_event(request, None, self.queryset.get(
                task_id=task_id, user_id=request.user.id), CREATE)

            return Response(status=HTTP_201_CREATED)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id=None, *args, **kwargs):
        # Get requester id and try to get the instance
        try:
            instance = self.queryset.get(
                user_id=request.user.id, task_id=task_id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        log_event(request, instance, None, DELETE)

        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class TaskSuggestionView(RetrieveAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSuggestionSerializer

    def retrieve(self, request, *args, **kwargs):
        if request.user.id == None:
            return Response(status=HTTP_401_UNAUTHORIZED)

        # Get user skills
        user_skills = Skill.objects.filter(users__user_id=request.user.id, users__is_preferred=True).distinct()

        # Get tasks with user_skills which the user has not already submitted
        # Exclude tasks created by the user
        tasks = self.queryset.filter(skills__skill__in=user_skills).exclude(
            submissions__user_id=request.user.id, project__user_id=request.user.id).distinct()

        serializer = self.serializer_class(
            tasks, context={'user_skills': user_skills}, many=True)

        return Response(serializer.data, status=HTTP_200_OK)


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskGETSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('title', 'description', 'skills__skill__name',)

    def create(self, request, *args, **kwargs):
        # Determine if user is project creator prior to create
        try:
            project_creator = Project.objects.get(
                id=request.data.get('project')).user_id

            if project_creator != request.user.id:
                raise ValueError('Requester permissions are too low.')
        except:
            return Response(status=HTTP_401_UNAUTHORIZED)

        # Create Task object
        task_serializer = TaskPOSTSerializer(data={
            'title': request.data.get('title'),
            'description': request.data.get('description'),
            'project': request.data.get('project')})

        if task_serializer.is_valid():
            task_serializer.save()

            instance = Task.objects.get(id=task_serializer.data.get('id'))

            log_event(request, None, instance, CREATE)

            return Response(TaskGETSerializer(instance).data, status=HTTP_201_CREATED)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        # Determine if user is project creator prior to update
        try:
            instance = self.queryset.get(id=pk)
            if instance.project.user_id != request.user.id:
                raise ValueError('Requester permissions are too low.')
        except ValueError:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        request.data['last_updated'] = timezone.now()
        serializer = TaskPOSTSerializer(
            self.queryset.get(id=pk), data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            log_event(request, instance, self.queryset.get(id=pk), UPDATE)

            return Response(TaskGETSerializer(Task.objects.get(id=pk), context={'requester_id': instance.project.user_id}).data, status=HTTP_200_OK)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        # Determine if requester is project creator prior to delete
        try:
            instance = self.queryset.get(id=pk)
            if instance.project.user_id != request.user.id:
                raise ValueError('Requester permissions are too low.')
        except ValueError:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        log_event(request, instance, None, DELETE)

        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)
