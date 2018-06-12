# Crowdsrc imports
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from crowdsrc.src.views import *
from crowdsrc.settings import CREATE

# Django imports
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED


class SubmissionReviewCreateView(CreateAPIView):
    queryset = SubmissionReview.objects.all()
    serializer_class = ReviewPOSTSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            instance = self.queryset.get(id=serializer.data.get('id'))

            log_event(request, None, instance, CREATE)

            skill_reviews = request.data.pop('skill_reviews')
            # Add reviews for the skills
            for entry in skill_reviews:
                skill_name = entry[0]
                rating = entry[1]

                serializer = SkillReviewPOSTSerializer(
                    data={'review': instance.id,
                          'skill': Skill.objects.get(name=skill_name).id,
                          'rating': rating})
                if serializer.is_valid():
                    serializer.save()

                    log_event(request, None, SubmissionSkillReview.objects.get(
                        id=serializer.data.get('id')), CREATE)

            return Response(status=HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class ReviewSuggestionView(RetrieveAPIView):
    queryset = TaskSubmission.objects.all()
    serializer_class = ReviewSuggestionSerializer

    def retrieve(self, request, *args, **kwargs):
        # Get user skills, try to pair with submissions that the user has not
        # yet reviewed
        # Submission should be on tasks that are relevant to the user skills
        user_skills = Skill.objects.filter(
            users__user_id=request.user.id, users__is_preferred=True).distinct()

        # Get tasks related to user skills which the user hasn't reviewed
        tasks = Task.objects.only('id').filter(skills__skill__in=user_skills).exclude(
            submissions__reviews__reviewer_id=request.user.id).values_list('id', flat=True)

        submissions = self.queryset.filter(task_id__in=tasks)

        return Response(self.serializer_class(submissions).data, status=HTTP_200_OK)
