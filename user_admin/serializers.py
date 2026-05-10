from rest_framework import serializers
from app.models import User,Recipe

class UserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id","email","name","is_active","image"]


class RecipeListSerializer(serializers.ModelSerializer):

    user_name = serializers.CharField(
        source = "user.name"
    )

    class Meta:
        model = Recipe
        fields=["id","title","created_at","image","user_name"]


class RecipeDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = "__all__"