from crowdsrc.src import views
from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.authtoken import views as rest_framework_views

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'profiles', views.ProfileViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'team-messages', views.TeamMessageViewSet)
router.register(r'team-members', views.TeamMemberViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^users/$', views.UserListView.as_view()),
    url(r'^users/(?P<pk>[0-9]+)/$', views.UserDetailedView.as_view()),
    url(r'^users/new/$', views.UserCreateView.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
	url(r'^authenticate/', rest_framework_views.obtain_auth_token, name='authenticate'),
    url(r'^validate-token/', views.ObtainUserFromAuthToken.as_view(), name='validate'),
    url(r'^contact/$', views.DispatchEmail.as_view(), name='contact'),
    url(r'^profiles/update/(?P<pk>[0-9]+)/$', views.ProfileUpdateView.as_view()),
]