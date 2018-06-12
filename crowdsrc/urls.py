from crowdsrc.src.views import *
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'projects', project_views.ProjectViewSet)
router.register(r'tasks', task_views.TaskViewSet)
router.register(r'team-messages', team_message_views.TeamMessageViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^search/$', GlobalSearchListView.as_view(), name='search'),

    # Username availability URL
    url(r'^check/(?P<username>[a-zA-Z0-9_\-]+)/$', CheckUsernameView.as_view()),

    # Crowd Request URLs
    url(r'^crowd/(?P<username>[a-zA-Z0-9_\-]+)/$', CrowdRequestCreateDestroyView.as_view()),
    url(r'^crowd/(?P<sender_username>[a-zA-Z0-9_\-]+)/response/$', CrowdRequestUpdateView.as_view()),

    # User account deletion URL
    url(r'^delete/user/$', DeleteUserView.as_view()),

    # User URLs
    url(r'^notifications/$', NotificationListView.as_view()),
    url(r'^users/$', UserListView.as_view()),
    url(r'^users/(?P<username>[a-zA-Z0-9_\-]+)/$', UserDetailedView.as_view()),
    url(r'^users/(?P<username>[a-zA-Z0-9_\-]+)/image/$', UserImageRetrieveUpdateView.as_view()),
    url(r'^users/(?P<username>[a-zA-Z0-9_\-]+)/block/$', BlockedUserView.as_view()),
    url(r'^users/(?P<username>[a-zA-Z0-9_\-]+)/crowd/$', UserCrowdListView.as_view()),
    url(r'^users/(?P<username>[a-zA-Z0-9_\-]+)/stats/$', UserStatsView.as_view()),
    
    # User Settings URLs
    url(r'^settings/users/$', UserSettingsRetrieveView.as_view()),
    url(r'^settings/users/privacy/$', UserPrivacySettingsUpdateView.as_view()),
    url(r'^settings/users/preferences/$', UserPreferencesUpdateView.as_view()),

    # User suggestions URL
    url(r'^suggest/reviews/$', ReviewSuggestionView.as_view()),
    url(r'^suggest/tasks/$', TaskSuggestionView.as_view()),

    # User task save/unsave URL
    url(r'^tasks/(?P<task_id>[0-9]+)/save/$', UserTaskView.as_view()),
    # Task submission URLs
    url(r'^tasks/(?P<task_id>[0-9]+)/submissions/$', TaskSubmissionListCreateView.as_view()),
    url(r'^tasks/(?P<task_id>[0-9]+)/submissions/(?P<submission_id>[0-9]+)/$', TaskSubmissionRetrieveUpdateDestroyView.as_view()),
    url(r'^submissions/(?P<id>[0-9]+)/$', SubmissionFileDataView.as_view()),
    # Submission Review create URL
    url(r'^reviews/$', SubmissionReviewCreateView.as_view()),

    # Project Message, Task, and Team list GET URLs
    url(r'^projects/(?P<id>[0-9]+)/messages/$', ProjectMessageView.as_view()),
    url(r'^projects/(?P<id>[0-9]+)/tasks/$', ProjectTaskView.as_view()),
    # Project Category URL
    url(r'^projects/(?P<project_id>[0-9]+)/categories/(?P<category_name>[a-zA-Z0-9_+\-\w ]+)/$', ProjectCategoryView.as_view()),

    # Skill URLs
    url(r'^skills/(?P<skill_name>[a-zA-Z0-9_+\-\w ]+)/$', SkillDetailView.as_view()),
    url(r'^users/skills/(?P<skill_name>[a-zA-Z0-9_+\-\w ]+)/$', UserSkillView.as_view()),
    url(r'^tasks/(?P<task_id>[0-9]+)/skills/(?P<skill_name>[a-zA-Z0-9_+\-\w ]+)/$', TaskSkillView.as_view()),

    # Team Message Reply URLs
    url(r'team-messages/(?P<message_id>[0-9]+)/replies/$', TeamMessageReplyCreateView.as_view()),
    url(r'team-messages/(?P<message_id>[0-9]+)/replies/(?P<reply_id>[0-9]+)/$', TeamMessageReplyRetrieveUpdateDestroyView.as_view()),

    # Email verification URLs
    url(r'verify/(?P<b64uid>.+)/(?P<token>.+)/$', EmailVerificationView.as_view()),
    url(r'verify/(?P<b64uid>.+)/$', ResendEmailVerificationView.as_view()),
    url(r'change-email/$', EmailChangeView.as_view()),

    # Password Reset URLs
    url(r'change-password/$', PasswordChangeView.as_view()),
    url(r'reset-password/$', RequestPasswordResetView.as_view()),
    url(r'reset-password/(?P<b64uid>.+)/$', PasswordResetView.as_view()),

    # Authentication and validation URLs
    url(r'authenticate/$', ObtainExpiringAuthToken.as_view()),
    url(r'refresh-token/$', RefreshExpiringAuthToken.as_view()),
    url(r'register/$', RegisterUserView.as_view()),

    # Contact form URL
    url(r'contact/$', DispatchEmail.as_view()),
]