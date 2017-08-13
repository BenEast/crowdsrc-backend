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

########## Category View Set ##########
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def list(self, request):
        queryset = Category.objects.all()
        serializer = CategorySerializer(
            queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Category.objects.all()
        category = get_object_or_404(queryset, pk=pk)
        serializer = CategorySerializer(
            category, context=self.get_serializer_context())
        return Response(serializer.data)
########## Category View Set ##########

########## User View Set ##########
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserListGETSerializer
    permission_classes = (AllowAny)

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return UserPOSTSerializer
        else:
            return self.serializer_class

    def list(self, request):
        queryset = User.objects.all()
        serializer = UserListGETSerializer(
            queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UserDetailedGETSerializer(
            user, context=self.get_serializer_context())
        return Response(serializer.data)
########## User View Set ##########

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
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileGETSerializer

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
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

########## Comment View Set ##########
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentGETSerializer

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return CommentPOSTSerializer
        else:
            return self.serializer_class

    def list(self, request):
        queryset = Comment.objects.all()
        serializer = CommentGETSerializer(
            queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Comment.objects.all()
        comment = get_object_or_404(queryset, pk=pk)
        serializer = CommentGETSerializer(
            comment, context=self.get_serializer_context())
        return Response(serializer.data)
########## Comment View Set ##########

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
