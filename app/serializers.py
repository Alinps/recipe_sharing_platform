from rest_framework import serializers
from app.models import Recipe
from app.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name']
class RecipeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only = True)
    class Meta:
        model = Recipe
        fields = ['id','title','image','user']

class UserSerializerDetailed(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
    
class RecipeSerializerDetailed(serializers.ModelSerializer):
    user = UserSerializerDetailed(read_only = True)
    class Meta:
        model = Recipe
        fields = '__all__'