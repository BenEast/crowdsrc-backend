# Crowdsrc imports
from crowdsrc.src.models import Category, ProjectCategory, Project, TeamMessageReply
from .user_serializers import UserListGETSerializer

# Django imports
from django.db.models import Count
from rest_framework.serializers import ModelSerializer, IntegerField, SerializerMethodField


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ('name',)


class ProjectListGETSerializer(ModelSerializer):
    user = UserListGETSerializer()

    categories = SerializerMethodField(read_only=True)
    message_count = SerializerMethodField(read_only=True)
    task_count = IntegerField(source='tasks.count', read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'created',
                  'last_updated', 'user', 'categories',
                  'message_count', 'task_count')

    def get_categories(self, obj):
        categories = Category.objects.filter(
            id__in=ProjectCategory.objects.filter(project_id=obj.id).values('category_id'))
        return CategorySerializer(categories, many=True).data

    def get_message_count(self, obj):
        message_count = obj.messages.distinct().count()
        reply_count = TeamMessageReply.objects.filter(
            message__project_id=obj.id).distinct().count()

        return message_count + reply_count


class ProjectDetailedGETSerializer(ModelSerializer):
    user = UserListGETSerializer()

    categories = SerializerMethodField()
    message_count = SerializerMethodField(read_only=True)
    task_count = IntegerField(source='tasks.count', read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'created',
                  'last_updated', 'website', 'user', 'categories',
                  'message_count', 'task_count')

    def get_categories(self, obj):
        categories = Category.objects.filter(
            id__in=ProjectCategory.objects.filter(project_id=obj.id).values('category_id'))
        return CategorySerializer(categories, many=True).data

    def get_message_count(self, obj):
        message_count = obj.messages.distinct().count()
        reply_count = TeamMessageReply.objects.filter(
            message__project_id=obj.id).distinct().count()

        return message_count + reply_count


class ProjectPOSTSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'created', 'last_updated',
                  'website', 'user')


class ProjectCategoryPOSTSerializer(ModelSerializer):
    class Meta:
        model = ProjectCategory
        fields = ('id', 'project', 'category')
