# Crowdsrc imports
from crowdsrc.src.serializers.skill_serializers import *
from crowdsrc.src.serializers.user_serializers import UserListGETSerializer
from crowdsrc.src.serializers.project_serializers import ProjectListGETSerializer
from crowdsrc.src.views.views import *
from crowdsrc.src.models import *
from crowdsrc.settings import CREATE, DELETE

# Django imports
from django.db.models import Count
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED


class SkillDetailView(RetrieveAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

    def retrieve(self, request, skill_name=None, *args, **kwargs):
        try:
            skill = Skill.objects.get(name=skill_name)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Determine if the user has the skill
        try:
            UserSkill.objects.get(user_id=request.user.id, skill_id=skill.id)
            user_has_skill = True
        except:
            user_has_skill = False

        # Get user_count, task_count, project_count
        user_count = UserSkill.objects.filter(skill_id=skill.id).count()
        task_count = TaskSkill.objects.filter(skill_id=skill.id).count()

        project_count = Project.objects.filter(
            id__in=Task.objects.filter(
                id__in=TaskSkill.objects.filter(
                    skill_id=skill.id).values('task_id')
            ).values('project_id')).distinct().count()

        # Get 5 projects w/ most tasks w/ this skill
        tasks = Task.objects.filter(id__in=TaskSkill.objects.filter(
            skill_id=skill.id).values('task_id'))
        top_projects = Project.objects.filter(
            id__in=tasks.values('project_id'))[:5]

        project_serializer = ProjectListGETSerializer(top_projects, many=True)

        # Get 5 users w/ this skill && working on most tasks w/ this skill
        top_users = User.objects.filter(
            id__in=UserSkill.objects.filter(
                skill_id=skill.id).values('user_id'))

        # Exclude users being blocked by the requester or that are blocking
        # the requester
        if not request.user.id == None:
            blocked = BlockedUser.objects.filter(
                source_id=request.user.id).values('target_id')
            blocking = BlockedUser.objects.filter(
                target_id=request.user.id).values('source_id')
            top_users.exclude(id__in=blocked).exclude(id__in=blocking)

        data = {'user_count': user_count, 'task_count': task_count, 'project_count': project_count,
                'user_has_skill': user_has_skill, 'top_projects': project_serializer.data,
                'top_users': UserListGETSerializer(top_users[:5], many=True).data}

        return Response(data, status=HTTP_200_OK)


class TaskSkillView(GenericAPIView, CreateModelMixin, DestroyModelMixin):
    queryset = TaskSkill.objects.all()
    serializer_class = TaskSkillPOSTSerializer

    def post(self, request, task_id=None, skill_name=None, *args, **kwargs):
        try:
            project_creator_id = Task.objects.get(id=task_id).project.user_id
            if project_creator_id != request.user.id:
                raise ValueError('Must be project creator')
        except ValueError:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Bad request if the skill is whitespace
        if skill_name.isspace() or not skill_name:
            return Response('Skill cannot be whitespace', status=HTTP_400_BAD_REQUEST)

        skill, _ = Skill.objects.get_or_create(name=skill_name)

        # Create the task skill since we're authorized
        serializer = self.serializer_class(
            data={'task': task_id, 'skill': skill.id})

        if serializer.is_valid():
            serializer.save()
            instance = self.queryset.get(id=serializer.data.get('id'))

            log_event(request, None, instance, CREATE)

            return Response(TaskSkillSerializer(instance).data, status=HTTP_201_CREATED)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, task_id=None, skill_name=None, *args, **kwargs):
        try:
            project_creator_id = Task.objects.get(id=task_id).project.user_id
            if project_creator_id != request.user.id:
                raise ValueError('Must be project creator')

            instance = self.queryset.get(
                task_id=task_id, skill__name=skill_name)
        except ValueError:
            return Response(status=HTTP_401_UNAUTHORIZED)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        log_event(request, instance, None, DELETE)

        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class UserSkillView(GenericAPIView, CreateModelMixin, DestroyModelMixin):
    queryset = UserSkill.objects.all()
    serializer_class = UserSkillPOSTSerializer

    def post(self, request, skill_name=None, *args, **kwargs):
        # Bad request if the skill name is whitespace
        if skill_name.isspace() or not skill_name:
            return Response('Skill cannot be whitespace', status=HTTP_400_BAD_REQUEST)

        skill, _ = Skill.objects.get_or_create(name=skill_name)

        # Add the user skill
        serializer = self.serializer_class(
            data={'user': request.user.id, 'skill': skill.id})

        if serializer.is_valid():
            serializer.save()
            instance = self.queryset.get(id=serializer.data.get('id'))

            log_event(request, None, instance, CREATE)

            return Response(UserSkillSerializer(instance, context={'requester_id': request.user.id}).data, status=HTTP_201_CREATED)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, skill_name=None, *args, **kwargs):
        try:
            instance = self.queryset.get(
                user_id=request.user.id, skill__name=skill_name)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        log_event(request, instance, None, DELETE)

        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)
