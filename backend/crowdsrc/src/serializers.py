from crowdsrc.src.models import Category, Comment, Project, Profile, Reply, Team, TeamMessage
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers

########## Category Serializers ##########
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'projects')
        depth = 2

class NestedCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description')
########## Category Serializers ##########

########## User Serializers ##########
class UserListGETSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined')

class UserDetailedGETSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'date_joined', 'last_login', 'projects', 'comments', 'profile')
        depth = 2

class UserPOSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password',
                  'email', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            password=make_password(validated_data['password']),
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        return user
########## User Serializers ##########

########## Profile Serializers ##########
class ProfileGETSerializer(serializers.ModelSerializer):
    user = UserDetailedGETSerializer()

    class Meta:
        model = Profile
        fields = ('id', 'user', 'bio', 'location', 'birth_date', 'image_name')
        depth = 1

class ProfilePOSTSerializer(serializers.ModelSerializer):
    user = UserPOSTSerializer()

    class Meta:
        model = Profile
        fields = ('id', 'user', 'bio', 'location', 'birth_date', 'image_name')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create(user_data)
        profile = Profile.objects.create(user=user, **validated_data)
        return profile
########## Profile Serializers ##########

########## Team Serializers ##########
class TeamGETSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'members', 'messages')
        depth = 2

class ReplyGETSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()

    class Meta:
        model = Reply
        fields = ('id', 'user', 'body', 'create_datetime')
        depth = 1

class TeamMessageGETSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()
    replies = ReplyGETSerializer()
    
    class Meta:
        model = TeamMessage
        fields = ('id', 'user', 'title', 'body', 'create_datetime', 'replies')
        depth = 2

########## Team Serializers ##########

########## Project Serializers ##########
class ProjectListGETSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()

    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'create_datetime',
                  'website', 'user', 'category')
        depth = 1
        
class ProjectDetailedGETSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()
    team = TeamGETSerializer() 
    
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'create_datetime',
                  'website', 'user', 'category', 'comments', 'team')
        depth = 2

class ProjectPOSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'create_datetime',
                  'website', 'user', 'category')
########## Project Serializers ##########

########## Comment Serializers ##########
class CommentGETSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'comment_body', 'create_datetime', 'user', 'project')

class CommentPOSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'comment_body', 'create_datetime', 'user', 'project')
########## Comment Serializers ##########