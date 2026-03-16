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
        fields = ['id', 'name', 'email', 'is_active',]
    
class RecipeSerializerDetailed(serializers.ModelSerializer):
    user = UserSerializerDetailed(read_only = True)
    class Meta:
        model = Recipe
        fields = '__all__'



class RecipeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'image']

class UserProfileSerializer(serializers.ModelSerializer):
    # This matches the 'related_name' in your Recipe model ForeignKey
    # If you didn't set a related_name, use 'recipe_set'
    recipes = RecipeProfileSerializer(source='recipe_set',many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'is_active', 'recipes']