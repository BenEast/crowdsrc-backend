# Crowdsrc imports
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from crowdsrc.settings import CREATE, DELETE
from .views import *

# Django imports
from django.db.models import Count, Prefetch
from rest_framework.generics import GenericAPIView, ListAPIView, UpdateAPIView
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter


class ProjectMessageView(ListAPIView):
    queryset = TeamMessage.objects.all()
    serializer_class = TeamMessageGETSerializer

    # Gets a list of team messages for the given project
    #
    # Does not return messages written by users that are blocking the
    # requester, or by users that the requester has blocked.
    def list(self, request, id=None):
        # Filter messages written by users that are blocking the requester
        blockers = BlockedUser.objects.filter(
            target_id=request.user.id).values('source_id')
        queryset = self.queryset.filter(
            project_id=id).exclude(user_id__in=blockers)

        # Filter messages written by users that the requester is blocking
        blocking = BlockedUser.objects.filter(
            source_id=request.user.id).values('target_id')
        queryset = queryset.exclude(user_id__in=blocking)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class ProjectTaskView(ListAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskGETSerializer

    # Gets a list of tasks for the specified project id
    def list(self, request, id=None):
        serializer = self.serializer_class(self.queryset.filter(project_id=id), many=True,
                                           context={'requester_id': request.user.id})
        return Response(serializer.data, status=HTTP_200_OK)


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectListGETSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ('title', 'description', 'website', 'categories__category__name',
                     'tasks__skills__skill__name')

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return ProjectPOSTSerializer
        else:
            return self.serializer_class

    # Retrieves a project by ID
    def retrieve(self, request, pk=None):
        project = Project.objects.get(id=pk)

        # Get 5 skills that appear in the most tasks on this project
        top_skills = TaskSkill.objects.filter(task__project_id=pk).values('skill').order_by('skill').annotate(
            skill_count=Count('skill')).order_by('-skill_count').values_list('skill__name', 'skill_count').distinct()[:5]

        serializer = ProjectDetailedGETSerializer(
            project, context=self.get_serializer_context())

        output = dict(serializer.data)
        output['skills'] = top_skills

        return Response(output, status=HTTP_200_OK,
                        headers=self.get_success_headers(serializer.data))

    # Updates a project iff the requesting user is the user that created
    # the project.
    def partial_update(self, request, pk=None):
        instance = self.queryset.get(id=pk)

        # Check auth token before performing the action
        if instance.user_id != request.user.id:
            return Response(status=HTTP_401_UNAUTHORIZED)

        request.data['last_updated'] = timezone.now()
        serializer = ProjectPOSTSerializer(
            self.queryset.get(id=pk), data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            log_event(request, instance, self.queryset.get(id=pk), UPDATE)

            return Response(ProjectDetailedGETSerializer(self.queryset.get(id=pk)).data, status=HTTP_200_OK)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    # Creates a new project if the requesting user is authenticated
    def create(self, request, *args, **kwargs):
        category_data = request.data.pop('categories')
        task_data = request.data.pop('tasks')

        request.data['user'] = request.user.id
        serializer = ProjectPOSTSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            instance = self.queryset.get(id=serializer.data.get('id'))

            log_event(request, None, instance, CREATE)

            # Create project categories objects
            for category_name in category_data:
                if not category_name or category_name.isspace():
                    continue

                category, _ = Category.objects.get_or_create(
                    name=category_name)

                category_serializer = ProjectCategoryPOSTSerializer(
                    data={'project': instance.id, 'category': category.id})

                if category_serializer.is_valid():
                    category_serializer.save()

                    log_event(request, None, ProjectCategory.objects.get(
                        id=category_serializer.data.get('id')), CREATE)

            # Create task objects
            for task in task_data:
                skill_data = task.pop('skills')

                task_serializer = TaskPOSTSerializer(
                    data={'project': instance.id, 'title': task.get('title'), 'description': task.get('description')})

                if task_serializer.is_valid():
                    task_serializer.save()
                    task = Task.objects.get(id=task_serializer.data.get('id'))

                    log_event(request, None, task, CREATE)

                    # Create task skill objects
                    for skill_name in skill_data:
                        if not skill_name or skill_name.isspace():
                            continue

                        skill, _ = Skill.objects.get_or_create(name=skill_name)
                        skill_serializer = TaskSkillPOSTSerializer(
                            data={'task': task.id, 'skill': skill.id})

                        if skill_serializer.is_valid():
                            skill_serializer.save()

                            log_event(request, None, TaskSkill.objects.get(
                                id=skill_serializer.data.get('id')), CREATE)

            return Response(serializer.data, status=HTTP_201_CREATED,
                            headers=self.get_success_headers(serializer.data))

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class ProjectCategoryView(GenericAPIView, CreateModelMixin, DestroyModelMixin):
    queryset = ProjectCategory.objects.all()
    serializer_class = ProjectCategoryPOSTSerializer

    def post(self, request, project_id=None, category_name=None, *args, **kwargs):
        try:
            project = Project.objects.get(id=project_id)
            if project.user_id != request.user.id:
                raise ValueError('Must be project creator')
        except ValueError:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        if category_name.isspace() or not category_name:
            return Response('Category cannot be whitespace', status=HTTP_400_BAD_REQUEST)

        category, _ = Category.objects.get_or_create(name=category_name)

        serializer = self.serializer_class(data={'project': project_id,
                                                 'category': category.id})
        if serializer.is_valid():
            serializer.save()

            log_event(request, None, self.queryset.get(
                id=serializer.data.get('id')), CREATE)

            return Response(CategorySerializer(category).data, status=HTTP_201_CREATED)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, project_id=None, category_name=None, *args, **kwargs):
        try:
            instance = ProjectCategory.objects.get(
                project_id=project_id, category__name=category_name)

            if instance.project.user_id != request.user.id:
                raise ValueError('Must be project creator')
        except ValueError:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        log_event(request, instance, None, DELETE)

        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)
