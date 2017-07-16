from crowdsrc.src.models import Category, Comment, Project, Profile
from django.contrib.auth.models import User
from rest_framework import serializers

########## Category Serializers ##########
class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('url', 'id', 'name', 'description', 'projects')
        depth = 1

class NestedCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('url', 'id', 'name', 'description')
########## Category Serializers ##########

########## User Serializers ##########
class UserDetailedSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'email', 'first_name', 'last_name', 
            'date_joined', 'last_login')
    
class UserSimpleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'email')
########## User Serializers ##########

########## Profile Serializers ##########
class ProfileGETSerializer(serializers.HyperlinkedModelSerializer):
    user = UserDetailedSerializer()
    class Meta:
        model = Profile
        fields = ('url', 'id', 'user', 'bio', 'location', 'birth_date', 'image_name')
        depth = 1
                    
class ProfilePOSTSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'user', 'bio', 'location', 'birth_date', 'image_name')
########## Profile Serializers ##########
            
########## Project Serializers ##########                
class ProjectDetailedGETSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSimpleSerializer()
    category = NestedCategorySerializer()
    class Meta:
        model = Project
        fields = ('url', 'id', 'title', 'description', 'create_datetime', 'website', 'user', 'category')        
        depth = 1
    
class ProjectSimpleGETSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSimpleSerializer()
    category = NestedCategorySerializer()
    class Meta:
        model = Project
        fields = ('url', 'id', 'title', 'create_datetime', 'user', 'category')        
        depth = 1

class ProjectPOSTSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'create_datetime', 'website', 'user', 'category')
########## Project Serializers ##########  
    
########## Comment Serializers ##########    
class CommentGETSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSimpleSerializer()
    project = ProjectSimpleGETSerializer()
    
    class Meta:
        model = Comment
        fields = ('url', 'id', 'comment_body', 'create_datetime', 'user', 'project')
        depth = 1

class CommentPOSTSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'comment_body', 'create_datetime', 'user', 'project')
########## Comment Serializers ########## 
