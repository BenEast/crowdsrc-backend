from math import ceil

# Crowdsrc imports
from crowdsrc.settings import ALPHA, BETA, DELTA
from crowdsrc.src.models import Skill, TaskSkill, UserSkill, TaskSubmission, SubmissionReview, SubmissionSkillReview

# Django imports
from rest_framework.serializers import ModelSerializer, SerializerMethodField


class SkillSerializer(ModelSerializer):
    class Meta:
        model = Skill
        fields = ('name',)


class TaskSkillSerializer(ModelSerializer):
    skill = SkillSerializer()

    class Meta:
        model = TaskSkill
        fields = ('skill',)


class TaskSkillPOSTSerializer(ModelSerializer):
    class Meta:
        model = TaskSkill
        fields = ('id', 'task', 'skill')


class UserSkillSerializer(ModelSerializer):
    skill = SkillSerializer()
    rating = SerializerMethodField(read_only=True)
    is_preferred = SerializerMethodField(read_only=True)

    class Meta:
        model = UserSkill
        fields = ('id', 'skill', 'rating', 'is_preferred')

    def get_is_preferred(self, obj):
        if self.context.get('requester_id') == obj.user_id:
            return obj.is_preferred
        else:
            return None

    def get_rating(self, obj):
        rating = 0

        user_submissions = TaskSubmission.objects.only('id').filter(
            user_id=obj.user_id).filter(task__skills__skill=obj.skill).distinct()

        # Get points from accepted submissions
        accepted_submissions = user_submissions.filter(is_accepted=True)
        rating += DELTA * len(accepted_submissions.values_list('id'))

        for submission_id in user_submissions.values_list('id', flat=True):
            # Get avg rating for each submission
            ratings = []
            reviews = SubmissionReview.objects.filter(
                submission_id=submission_id).distinct()

            for review_id in reviews.values_list('id', flat=True):
                review_rating = SubmissionReview.objects.only('rating').get(
                    id=review_id).rating
                skill_rating = SubmissionSkillReview.objects.only('rating').get(
                    review_id=review_id, skill_id=obj.skill_id).rating

                ratings.append(
                    ceil(ALPHA * review_rating + BETA * skill_rating))

            if len(ratings):
                rating += ceil(sum(ratings) / len(ratings))

        return rating


class UserSkillPOSTSerializer(ModelSerializer):
    class Meta:
        model = UserSkill
        fields = ('id', 'user', 'skill')
