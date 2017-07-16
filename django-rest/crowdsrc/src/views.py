from crowdsrc.src.models import Category, Comment, Project, User, Profile
from crowdsrc.src.serializers import *
from django.shortcuts import get_object_or_404
from django.views.generic.edit import CreateView
from rest_framework import viewsets
from rest_framework.response import Response

########## Category View Set ##########
class CategoryViewSet(viewsets.ModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer
	
	def list(self, request):
		queryset = Category.objects.all()
		serializer = CategorySerializer(queryset, many=True, context=self.get_serializer_context())
		return Response(serializer.data)

	def retrieve(self, request, pk=None):
		queryset = Category.objects.all()
		category = get_object_or_404(queryset, pk=pk)
		serializer = CategorySerializer(category, context=self.get_serializer_context())
		return Response(serializer.data)
########## Category View Set ##########

########## User View Set ##########
class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSimpleSerializer
	
	def get_serializer_class(self):
		if self.request.method in ('POST', 'PATCH'):
			return UserDetailedSerializer
		else:
			return self.serializer_class

	def list(self, request):
		queryset = User.objects.all()
		serializer = UserSimpleSerializer(queryset, many=True, context=self.get_serializer_context())
		return Response(serializer.data)

	def retrieve(self, request, pk=None):
		queryset = User.objects.all()
		user = get_object_or_404(queryset, pk=pk)
		serializer = UserDetailedSerializer(user, context=self.get_serializer_context())
		return Response(serializer.data)
########## User View Set ##########

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
		serializer = ProfileGETSerializer(queryset, many=True, context=self.get_serializer_context())
		return Response(serializer.data)

	def retrieve(self, request, pk=None):
		queryset = Profile.objects.all()
		profile = get_object_or_404(queryset, pk=pk)
		serializer = ProfileGETSerializer(profile, context=self.get_serializer_context())
		return Response(serializer.data)
########## Profile View Set ##########

########## Project View Set ##########
class ProjectViewSet(viewsets.ModelViewSet):
	queryset = Project.objects.all()
	serializer_class = ProjectSimpleGETSerializer
	
	def get_serializer_class(self):
		if self.request.method in ('POST', 'PATCH'):
			return ProjectPOSTSerializer
		else:
			return self.serializer_class
	
	def list(self, request):
		queryset = Project.objects.all()
		serializer = ProjectSimpleGETSerializer(queryset, many=True, context=self.get_serializer_context())
		return Response(serializer.data)

	def retrieve(self, request, pk=None):
		queryset = Project.objects.all()
		project = get_object_or_404(queryset, pk=pk)
		serializer = ProjectDetailedGETSerializer(project, context=self.get_serializer_context())
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
		serializer = CommentGETSerializer(queryset, many=True, context=self.get_serializer_context())
		return Response(serializer.data)

	def retrieve(self, request, pk=None):
		queryset = Comment.objects.all()
		comment = get_object_or_404(queryset, pk=pk)
		serializer = CommentGETSerializer(comment, context=self.get_serializer_context())
		return Response(serializer.data)
########## Comment View Set ##########

###########################################################################
# Custom getters for various purposes
###########################################################################


