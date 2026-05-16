from rest_framework import serializers
from app.models import User,Recipe

class UserListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id","email","name","is_active","image","created_at"]
    
    def get_image(self, obj):
        if obj.image:
            return obj.image.url   
        return None

    
    


class RecipeListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  

    user_name = serializers.CharField(
        source = "user.name"
    )

    class Meta:
        model = Recipe
        fields=["id","title","created_at","image","user_name"]


    def get_image(self, obj):
        if obj.image:
            return obj.image.url   
        return None
    


class RecipeDetailSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  
    class Meta:
        model = Recipe
        fields = "__all__"

    def get_image(self, obj):
        if obj.image:
            return obj.image.url   
        return None