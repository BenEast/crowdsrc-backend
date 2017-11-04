from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.views.generic.edit import CreateView
from rest_framework import generics, viewsets
from rest_framework.decorators import detail_route, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

########## User Views ##########
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListGETSerializer
    permission_classes = (AllowAny,)

    def list(self, request):
        queryset = User.objects.all()
        serializer = UserListGETSerializer(
            queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

class UserDetailedView(generics.RetrieveDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailedGETSerializer
    permission_classes = (AllowAny,)

    def retrieve(self, request, pk=None):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UserDetailedGETSerializer(
            user, context=self.get_serializer_context())
        return Response(serializer.data)

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserPOSTSerializer
    permission_classes = (AllowAny,)
########## User Views ##########

########## Profile View Set ##########
class ProfileUpdateView(generics.UpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfilePUTSerializer
    permission_classes = ()

    def put(self, request, pk, format=None):
        profile = get_object_or_404(Profile.objects.all(), pk=pk)
        serializer = ProfilePUTSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileGETSerializer

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', 'PUT'):
            return ProfilePOSTSerializer
        else:
            return self.serializer_class

    def list(self, request):
        queryset = Profile.objects.all()
        serializer = ProfileGETSerializer(
            queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Profile.objects.all()
        profile = get_object_or_404(queryset, pk=pk)
        serializer = ProfileGETSerializer(
            profile, context=self.get_serializer_context())
        return Response(serializer.data)

    def update(self, request, pk=None):
        queryset = Profile.objects.all()
        profile = get_object_or_404(queryset, pk=pk)
        serializer = ProfilePOSTSerializer(profile, data=request.data, partial=True)
        return Response(serializer.data)
########## Profile View Set ##########

########## Project View Set ##########
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectListGETSerializer

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return ProjectPOSTSerializer
        else:
            return self.serializer_class

    def list(self, request):
        queryset = Project.objects.all()
        serializer = ProjectListGETSerializer(
            queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Project.objects.all()
        project = get_object_or_404(queryset, pk=pk)
        serializer = ProjectDetailedGETSerializer(
            project, context=self.get_serializer_context())
        return Response(serializer.data)
########## Project View Set ##########

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

class TeamMessageViewSet(viewsets.ModelViewSet):
    queryset = TeamMessage.objects.all()
    serializer_class = TeamMessageGETSerializer

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return TeamMessagePOSTSerializer
        else:
            return self.serializer_class

class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer

###########################################################################
# Custom endpoints for various purposes
###########################################################################

# Get user given a valid auth token
class ObtainUserFromAuthToken(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        token = Token.objects.get(key=request.data['token'])
        return Response({'user_id': token.user_id})

# Dispatch an email based on post request
class DispatchEmail(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserListGETSerializer
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        message = 'Email: ' + request.data['email']
        message += '\nUsername: ' + request.data['username']
        message += '\nName: ' + request.data['name']
        message += '\nMessage: ' + request.data['message']

        return Response({'response': send_mail('Crowdsrc Contact from ' + request.data['username'], message,
                                               'contact.crowdsrc@gmail.com', ['ben.east22@gmail.com'], fail_silently=False)})
