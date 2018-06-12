# Crowdsrc imports
from crowdsrc.src.models import *

# Django imports
from django.db.models import Count
from rest_pandas import PandasView, PandasSerializer, PandasJSONRenderer
from rest_framework.serializers import IntegerField, ModelSerializer, SerializerMethodField


class UserPandasSerializer(ModelSerializer):
    review_count = IntegerField(source='reviews.count')
    submission_count = SerializerMethodField()
    accepted_submission_count = SerializerMethodField()
    average_rating = SerializerMethodField()

    class Meta:
        model = Skill
        fields = ('name', 'review_count', 'submission_count',
                  'accepted_submission_count', 'average_rating')
        pandas_index = 'name'

    def get_submissions(self, obj):
        return TaskSubmission.objects.filter(task__skills__skill__id=obj.id, user__username=self.context.get('username'))

    def get_accepted_submission_count(self, obj):
        return self.get_submissions(obj).filter(is_accepted=True).count()

    def get_average_rating(self, obj):
        submissions = self.get_submissions(obj).only(
            'id').values_list('id', flat=True)

        ratings = list(SubmissionSkillReview.objects.only('rating').filter(
            skill_id=obj.id, review__submission_id__in=submissions).values_list('rating', flat=True))

        if len(ratings):
            return sum(ratings) / len(ratings)
        else:
            return 0

    def get_submission_count(self, obj):
        return self.get_submissions(obj).count()


class UserStatsView(PandasView):
    queryset = Skill.objects.all()
    serializer_class = UserPandasSerializer
    pandas_serializer_class = PandasSerializer
    renderer_classes = [PandasJSONRenderer, ]

    def get_serializer_context(self):
        return {'username': self.kwargs.get('username')}

    def filter_queryset(self, queryset):
        return queryset.filter(users__user__username=self.kwargs.get('username'))
