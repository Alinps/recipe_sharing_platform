from rest_framework import serializers
from app.models import Recipe
from app.models import User,WishList
import cloudinary.uploader


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name']




class RecipeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    image = serializers.SerializerMethodField()  # ADD THIS

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'image', 'user']

    def get_image(self, obj):
        if obj.image:
            return obj.image.url   # FULL CLOUDINARY URL
        return None
    




class UserSerializerDetailed(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'is_active',]




    
class RecipeSerializerDetailed(serializers.ModelSerializer):
    user = UserSerializerDetailed(read_only=True)
    is_saved = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()  

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_image(self, obj):
        if obj.image:
            return obj.image.url  
        return None

    def get_is_saved(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return WishList.objects.filter(user=user, recipe=obj).exists()
        return False





class RecipeProfileSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'image']

    def get_image(self, obj):
        if obj.image:
            return obj.image.url  
        return None
    


class WhilistSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishList
        fields = "__all__"


class ProfileSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()  

    class Meta:
        model = User
        fields = ["name", "email", "image"]

    def get_image(self, obj):
        if obj.image:
            return obj.image.url  
        return None

    def validate_email(self, value):
        user = self.instance

        if User.objects.exclude(pk=user.pk).filter(email=value).exists():  # type: ignore
            raise serializers.ValidationError("Email already exists")

        return value





class UserProfileSerializer(serializers.ModelSerializer):
    recipes = RecipeProfileSerializer(
        source='recipe_set',
        many=True,
        read_only=True
    )

    
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'is_active', 'recipes', 'image']
        read_only_fields = ['id', 'is_active', 'recipes']

    #Handle update (delete old image before replacing)
    def update(self, instance, validated_data):
        new_image = validated_data.get('image')

        # If new image uploaded → delete old one
        if new_image and instance.image:
            try:
                cloudinary.uploader.destroy(instance.image.public_id)
            except Exception as e:
                print("Cloudinary delete error:", e)

        return super().update(instance, validated_data)

    # Ensure frontend gets full Cloudinary URL
    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.image:
            data['image'] = instance.image.url
        else:
            data['image'] = None

        return data





