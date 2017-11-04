from crowdsrc.src.models import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers

########## User Serializers ##########
class UserListGETSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined')

class UserDetailedGETSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'date_joined', 'last_login', 'projects', 'profile')
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
        fields = ('id', 'user', 'bio', 'location', 'skills', 'birth_date', 'image_name')
        depth = 1

class ProfilePOSTSerializer(serializers.ModelSerializer):
    user = UserPOSTSerializer()

    class Meta:
        model = Profile
        fields = ('id', 'user', 'bio', 'location', 'skills', 'birth_date', 'image_name')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create(user_data)
        profile = Profile.objects.create(user=user, **validated_data)
        return profile

class ProfilePUTSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'user', 'bio', 'location', 'skills', 'birth_date', 'image_name')
########## Profile Serializers ##########

########## Team Serializers ##########
class TeamMessageGETSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()

    class Meta:
        model = TeamMessage
        fields = ('id', 'team', 'user', 'body', 'create_datetime', 'is_public')
        depth = 1

class TeamMessagePOSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMessage
        fields = ('id', 'team', 'user', 'body', 'create_datetime', 'is_public')

class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()

    class Meta:
        model = TeamMember
        fields = ('id', 'user', 'role')
        depth = 1
        
class TeamDetailedGETSerializer(serializers.ModelSerializer):
    members = TeamMemberSerializer(many=True)
    messages = TeamMessageGETSerializer(many=True)

    class Meta:
        model = Team
        fields = ('id', 'members', 'messages', 'is_public')
        depth = 2

class TeamListGETSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    message_count = serializers.IntegerField(source='messages.count', read_only=True)

    class Meta:
        model = Team
        fields = ('id', 'is_public', 'member_count', 'message_count')

########## Team Serializers ##########

########## Task Serializers ##########
class TaskMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskMember
        fields = ('id', 'member')
        depth = 2
        
class TaskSerializer(serializers.ModelSerializer):
    members = TaskMemberSerializer(many=True)
    class Meta:
        model = Task
        fields = ('id', 'project', 'title', 'description', 'status', 
                  'last_updated', 'skills', 'members', 'is_public')
        depth = 3
########## Task Serializers ##########

########## Project Serializers ##########
class ProjectListGETSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()
    team = TeamListGETSerializer()
    task_count = serializers.IntegerField(source='tasks.count', read_only=True)
    
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'create_datetime',
                  'website', 'user', 'category', 'team', 'task_count')
        depth = 1
        
class ProjectDetailedGETSerializer(serializers.ModelSerializer):
    user = UserListGETSerializer()
    team = TeamDetailedGETSerializer() 
    tasks = TaskSerializer(many=True)

    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'create_datetime',
                  'website', 'user', 'category', 'team', 'tasks')
        depth = 4

class ProjectPOSTSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'create_datetime',
                  'website', 'user', 'category')
########## Project Serializers ##########