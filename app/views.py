from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import User,Recipe
from .serializers import RecipeSerializer,RecipeSerializerDetailed, UserProfileSerializer
from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['POST'])
@permission_classes((AllowAny,))
def Signup(request):
    email  = request.data.get("email")
    password = request.data.get("password")
    name = request.data.get("name")
    if not name or not email or not password:
        return Response({'message':'All fields are required'})
      # validate password
    try:
        validate_password(password)
    except ValidationError as e:
        return Response(
            {"message": e.messages},
            status=status.HTTP_400_BAD_REQUEST
        )
    if User.objects.filter(email=email).exists():
        return  JsonResponse({'message':'Email already exist'} ,status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(email=email,password=password) # pyright: ignore[reportAttributeAccessIssue]
    user.name = name
    user.save()
    return JsonResponse({'message':'user created successsfully'} ,status = 200)





@api_view(["POST"])
@permission_classes((AllowAny,))
def Login_user(request):
    email = request.data.get("email")
    password = request.data.get("password")
    if email is None or password is None:
        return Response({'message': 'Please provide both username and password'},
                        status=HTTP_400_BAD_REQUEST)
    user = authenticate(email=email, password=password)
    if not user:
        return Response({'message': 'Invalid Credentials'},
                        status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key},status=HTTP_200_OK)



@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def create_recipe(request):
    user = request.user
    title = request.data.get("title")
    ingredients = request.data.get("ingredients")
    steps = request.data.get("steps")
    cooking_time = request.data.get("cooking_time")
    difficulty_level = request.data.get("difficulty_level")
    image = request.FILES.get("image")


    if not title or not ingredients or not steps or not cooking_time or not difficulty_level or not image:
        return JsonResponse({"message":"all fields are required"})
    recipes = Recipe.objects.create(
        user = user,
        title = title,
        ingredients = ingredients,
        steps = steps,
        cooking_time = cooking_time,
        difficulty_level = difficulty_level,
        image = image
    )
    recipes.save()
    return JsonResponse({"message":"Recipe created successfully"},status = 200)


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def list_recipe(request):
#     recipes = Recipe.objects.all()
#     serializer = RecipeSerializer(recipes,many=True)
#     return Response({'recipes':serializer.data},status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_recipe(request):
    # Use select_related to join the User table and Recipe table in one query
    recipes = Recipe.objects.select_related('user').all()
    
    serializer = RecipeSerializer(recipes, many=True)
    return Response({'recipes': serializer.data}, status=200)




# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def recipe_details(request,pk):
#     try:
#         recipe = Recipe.objects.get(pk = pk)
#     except:
#         return Response({"message":"Recipe not found"},status=404)
#     serializer = RecipeSerializerDetailed(recipe)
#     return Response({"data":serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recipe_details(request, pk):
    # Using select_related here makes it 1 query instead of 2
    recipe = Recipe.objects.select_related('user').filter(pk=pk).first()
    
    if not recipe:
        return Response({"message": "Recipe not found"}, status=404)
        
    serializer = RecipeSerializerDetailed(recipe)
    return Response({"data": serializer.data})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_recipe(request,pk):
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        return Response({"message":"Recipe cannot be deleted"},status=404)
    recipe.delete()
    return Response({"message":"Recipe has been Successfully deleted"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recipe_search(request):
    qtitle = request.query_params.get('qtitle','')
    recipes = Recipe.objects.select_related('user').filter(title__icontains=qtitle)
    if not recipes:
        return Response({"message":"no items found"})
    serializer = RecipeSerializerDetailed(recipes,many=True)
    return Response({"data":serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def password_change(request):
    user = request.user

    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")

    # check current password
    if not user.check_password(current_password):
        return Response(
            {"message": "Current password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ensure new password is different
    if user.check_password(new_password):
        return Response(
            {"message": "New password must be different from current password."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # validate password
    try:
        validate_password(new_password)
    except ValidationError as e:
        return Response(
            {"message": e.messages},
            status=status.HTTP_400_BAD_REQUEST
        )

    # set password correctly
    user.set_password(new_password)
    user.save()

    return Response({"message": "Password changed successfully."})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_recipe(request):
    pk = request.data.get("recipe_id")
    try:
        recipe = Recipe.objects.get(id=pk)
    except Recipe.DoesNotExist:
        return Response({"message":"Recipe not found"},status=status.HTTP_400_BAD_REQUEST)
    title = request.data.get('title')
    ingredients = request.data.get('ingredients')
    steps = request.data.get('steps')
    cooking_time = request.data.get('cooking_time')
    difficulty_level = request.data.get('difficulty')
    image = request.FILES.get('image')

    if title:
        recipe.title = title
    if ingredients:
        recipe.ingredients = ingredients
    if steps:
        recipe.steps = steps
    if cooking_time:
        recipe.cooking_time = cooking_time
    if difficulty_level:
        recipe.difficulty_level = difficulty_level
    if image:
        recipe.image = image
    recipe.save()
    return Response({"message":"Recipe updated successfully"},status=status.HTTP_200_OK)








OPENROUTER_API_KEY = "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"


@api_view(["POST"])
@permission_classes([AllowAny])
def chatbot(request):

    user_message = request.data.get("message")

    prompt = f"""
                You are a helpful cooking assistant for a recipe sharing platform.
                User question:{user_message}
            """

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a cooking expert assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()

    reply = result["choices"][0]["message"]["content"]

    return Response({"reply": reply})

    


@api_view(["GET"])
@permission_classes([AllowAny])
def user_profile(request,user_id):
    user = get_object_or_404(
        User.objects.prefetch_related('recipe_set'),
        id=user_id
    )
    serializer = UserProfileSerializer(user)
    return Response(serializer.data)
    