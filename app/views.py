from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import User,Recipe, WishList
from .serializers import ProfileSerializer, RecipeSerializer,RecipeSerializerDetailed, UserProfileSerializer
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
from django.db.models import Q
from .utils.pagination import RecipePagination
import logging
import time
from django.core.files.storage import default_storage
import os

logger = logging.getLogger("recipe_app")



@api_view(['POST'])
@permission_classes((AllowAny,))
def Signup(request):

    email = request.data.get("email")
    password = request.data.get("password")
    name = request.data.get("name")

    # mask email for privacy
    masked_email = email[:3] + "***" if email else "unknown"

    logger.info(f"Signup attempt | email={masked_email}")

    try:
        #  check required fields
        if not name or not email or not password:
            logger.warning(f"Signup failed | reason=missing_fields | email={masked_email}")
            return Response(
                {'message': 'All fields are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        #  validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            logger.warning(
                f"Signup failed | reason=weak_password | email={masked_email} | details={e.messages}"
            )
            return Response(
                {"message": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )

        #  check duplicate email
        if User.objects.filter(email=email).exists():
            logger.warning(
                f"Signup failed | reason=email_exists | email={masked_email}"
            )
            return JsonResponse(
                {'message': 'Email already exist'},
                status=status.HTTP_400_BAD_REQUEST
            )

        #  create user
        user = User.objects.create_user(email=email, password=password)  # type: ignore
        user.name = name
        user.save()

        logger.info(f"Signup successful | user={user.id}")

        return JsonResponse(
            {'message': 'User created successfully'},
            status=200
        )

    except Exception as e:
        logger.exception(
            f"Signup error | email={masked_email} | error={str(e)}"
        )
        return Response(
            {"error": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )







@api_view(["POST"])
@permission_classes((AllowAny,))
def Login_user(request):

    email = request.data.get("email")
    password = request.data.get("password")

    # mask email partially for privacy
    masked_email = email[:3] + "***" if email else "unknown"

    logger.info(f"Login attempt | email={masked_email}")

    try:
        # missing credentials
        if email is None or password is None:
            logger.warning(f"Login failed | reason=missing_credentials | email={masked_email}")
            return Response(
                {'message': 'Please provide both username and password'},
                status=HTTP_400_BAD_REQUEST
            )

        #  authenticate user
        user = authenticate(email=email, password=password)

        if not user:
            logger.warning(f"Login failed | reason=invalid_credentials | email={masked_email}")
            return Response(
                {'message': 'Invalid Credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        #  generate token
        token, _ = Token.objects.get_or_create(user=user)

        logger.info(f"Login successful | user={user.id}") # type: ignore

        return Response({
            "token": token.key,
            "user": {
                "id": user.id, # type: ignore
                "name": user.name # type: ignore
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(
            f"Login error | email={masked_email} | error={str(e)}"
        )
        return Response(
            {"error": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def create_recipe(request):
    user = request.user

    print("STORAGE:", default_storage.__class__)
    print("CLOUD NAME:", os.environ.get("CLOUDINARY_CLOUD_NAME"))
    print("FILES:", request.FILES)

    logger.info(f"Create recipe request | user={user.id}")
    try:
        title = request.data.get("title")
        ingredients = request.data.get("ingredients")
        steps = request.data.get("steps")
        cooking_time = request.data.get("cooking_time")
        difficulty_level = request.data.get("difficulty_level")
        description = request.data.get("description")
        image = request.FILES.get("image")


        if not title or not ingredients or not steps or not cooking_time or not difficulty_level or not image or not description:
            return JsonResponse({"message":"all fields are required"})
        recipes = Recipe.objects.create(
            user = user,
            title = title,
            ingredients = ingredients,
            steps = steps,
            cooking_time = cooking_time,
            difficulty_level = difficulty_level,
            description = description,
            image = image
        )
        recipes.save()
        print("IMAGE URL:", recipes.image.url)
        logger.info(f"Recipe created | user={user.id} | recipe_id={recipes.id}") # type: ignore
        return Response({"message":"Recipe created successfully"},status = 200)
    except Exception as e:
        logger.error(f"Error creating recipe | user={user.id} | error={str(e)}")
        return Response({"error": "Something went wrong"}, status=500)



# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def list_recipe(request):
#     recipes = Recipe.objects.all()
#     serializer = RecipeSerializer(recipes,many=True)
#     return Response({'recipes':serializer.data},status=200)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_recipe(request):

    user = request.user.id if request.user.is_authenticated else "anon"
    search_query = request.GET.get("search")
    logger.info(f"List recipes request | user={user} | search={search_query}")

    try:
        # Base queryset
        queryset = Recipe.objects.select_related('user').all()

        # Apply search filter
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(ingredients__icontains=search_query)
            )
            logger.info(f"Search applied | query='{search_query}'")

        total_count = queryset.count()

        # Pagination
        paginator = RecipePagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = RecipeSerializer(paginated_queryset, many=True)

        logger.info(
            f"Recipes fetched | user={user} | total={total_count} | returned={len(serializer.data)}"
        )

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        logger.exception(
            f"Error fetching recipes | user={user} | error={str(e)}"
        )
        return Response(
            {"error": "Something went wrong"},
            status=500
        )



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

    user = request.user.id
    logger.info(f"Recipe detail request | user={user} | recipe_id={pk}")

    try:
        # Using select_related for optimization
        recipe = Recipe.objects.select_related('user').filter(pk=pk).first()

        if not recipe:
            logger.warning(f"Recipe not found | user={user} | recipe_id={pk}")
            return Response({"message": "Recipe not found"}, status=404)

        serializer = RecipeSerializerDetailed(
            recipe, context={'request': request}
        )

        logger.info(f"Recipe fetched | user={user} | recipe_id={pk}")

        return Response({"data": serializer.data})

    except Exception as e:
        logger.exception(
            f"Error fetching recipe | user={user} | recipe_id={pk} | error={str(e)}"
        )
        return Response(
            {"error": "Something went wrong"},
            status=500
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_recipe(request,pk):
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        return Response({"message":"Recipe cannot be deleted"},status=404)
    if recipe.user != request.user:
        return Response(
            {"error": "Not authorized"},
            status=403
        )
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

    logger.info(f"Password change attempt | user={user.id}")

    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")

    try:
        # check current password
        if not user.check_password(current_password):
            logger.warning(f"Incorrect current password | user={user.id}")
            return Response(
                {"message": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        #  ensure new password is different
        if user.check_password(new_password):
            logger.warning(f"New password same as old | user={user.id}")
            return Response(
                {"message": "New password must be different from current password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        #  validate password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            logger.warning(
                f"Password validation failed | user={user.id} | reasons={e.messages}"
            )
            return Response(
                {"message": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )

        #  set password
        user.set_password(new_password)
        user.save()

        logger.info(f"Password changed successfully | user={user.id}")

        return Response({"message": "Password changed successfully."})

    except Exception as e:
        logger.exception(
            f"Error changing password | user={user.id} | error={str(e)}"
        )
        return Response(
            {"error": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_recipe(request):
    user = request.user.id
    pk = request.data.get("recipe_id")

    logger.info(f"Edit recipe request | user={user} | recipe_id={pk}")

    try:
        recipe = Recipe.objects.get(id=pk)
    except Recipe.DoesNotExist:
        logger.warning(f"Recipe not found | user={user} | recipe_id={pk}")
        return Response(
            {"message": "Recipe not found"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        updated_fields = []

        title = request.data.get('title')
        ingredients = request.data.get('ingredients')
        steps = request.data.get('steps')
        cooking_time = request.data.get('cooking_time')
        difficulty_level = request.data.get('difficulty')
        description = request.data.get('description')
        image = request.FILES.get('image')

        if title:
            recipe.title = title
            updated_fields.append("title")

        if ingredients:
            recipe.ingredients = ingredients
            updated_fields.append("ingredients")

        if steps:
            recipe.steps = steps
            updated_fields.append("steps")

        if cooking_time:
            recipe.cooking_time = cooking_time
            updated_fields.append("cooking_time")

        if difficulty_level:
            recipe.difficulty_level = difficulty_level
            updated_fields.append("difficulty_level")
        if description:
            recipe.description = description
            updated_fields.append("description")

        if image:
            recipe.image = image
            updated_fields.append("image")
        

        recipe.save()

        logger.info(
            f"Recipe updated | user={user} | recipe_id={pk} | fields={updated_fields}"
        )

        return Response(
            {"message": "Recipe updated successfully"},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception(
            f"Error updating recipe | user={user} | recipe_id={pk} | error={str(e)}"
        )
        return Response(
            {"error": "Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )








OPENROUTER_API_KEY = "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"




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chatbot(request):

    requester = request.user.id if request.user.is_authenticated else "anon"
    user_message = request.data.get("message", "")

    message_length = len(user_message) if user_message else 0

    logger.info(
        f"Chatbot request | requester={requester} | message_length={message_length}"
    )

    try:
        prompt = f"""
        You are a helpful cooking assistant for a recipe sharing platform.
        User question: {user_message}
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

        start_time = time.time()

        response = requests.post(url, headers=headers, json=data)

        duration = time.time() - start_time

        logger.info(
            f"Chatbot API call completed | requester={requester} | status={response.status_code} | time={duration:.2f}s"
        )

        result = response.json()

        if "choices" in result:
            reply = result["choices"][0]["message"]["content"]

            logger.info(
                f"Chatbot response success | requester={requester}"
            )

        else:
            error_msg = result.get("error", {}).get("message", "Unknown error")

            logger.warning(
                f"Chatbot API error | requester={requester} | error={error_msg}"
            )

            reply = error_msg

        return Response({"reply": reply})

    except Exception as e:
        logger.exception(
            f"Chatbot failure | requester={requester} | error={str(e)}"
        )
        return Response(
            {"error": "Chatbot service unavailable"},
            status=500
        )
    





@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request, user_id):

    requester = request.user.id if request.user.is_authenticated else "anon"

    logger.info(
        f"User profile request | requester={requester} | target_user={user_id}"
    )

    try:
        user = get_object_or_404(
            User.objects.prefetch_related('recipe_set'),
            id=user_id
        )

        serializer = UserProfileSerializer(user)

        logger.info(
            f"User profile fetched | requester={requester} | target_user={user_id}"
        )

        return Response(serializer.data)

    except Exception as e:
        # Note: get_object_or_404 raises Http404 → will also be caught here
        logger.exception(
            f"Error fetching user profile | requester={requester} | target_user={user_id} | error={str(e)}"
        )
        return Response(
            {"error": "Something went wrong"},
            status=500
        )




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_wishlist(request, user_id):

    requester = request.user.id
    logger.info(
        f"Wishlist request | requester={requester} | target_user={user_id}"
    )

    try:
        wishlist = WishList.objects.filter(user_id=user_id).select_related("recipe")
        recipes = [item.recipe for item in wishlist]
        count = len(recipes)

        if count == 0:
            logger.info(
                f"Wishlist empty | requester={requester} | target_user={user_id}"
            )
        else:
            logger.info(
                f"Wishlist fetched | requester={requester} | target_user={user_id} | count={count}"
            )

        serializer = RecipeSerializer(recipes, many=True)

        return Response(serializer.data)

    except Exception as e:
        logger.exception(
            f"Error fetching wishlist | requester={requester} | target_user={user_id} | error={str(e)}"
        )
        return Response(
            {"error": "Something went wrong"},
            status=500
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_wishlist(request):
    user = request.user
    recipe_id = request.data.get("recipe_id")

    recipe = get_object_or_404(Recipe, id=recipe_id)

    wishlist_item = WishList.objects.filter(
        user=user,
        recipe=recipe
    ).first()

    if wishlist_item:
        wishlist_item.delete()
        return Response({"status": "removed"})
    else:
        WishList.objects.create(user=user, recipe=recipe)
        return Response({"status": "added"})

     
    

    





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):

    user = request.user.id

    logger.info(f"Logout attempt | user={user}")

    try:
        # Delete the user's token
        request.user.auth_token.delete()

        logger.info(f"Logout successful | user={user}")

        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception(
            f"Logout failed | user={user} | error={str(e)}"
        )

        return Response(
            {"error": "Logout failed"},
            status=status.HTTP_400_BAD_REQUEST
        )
    





@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile(request):

    user = request.user
    user_id = user.id

    if request.method == "GET":
        logger.info(f"Profile fetch request | user={user_id}")

        try:
            serializer = ProfileSerializer(user)

            logger.info(f"Profile fetched | user={user_id}")

            return Response(serializer.data)

        except Exception as e:
            logger.exception(
                f"Error fetching profile | user={user_id} | error={str(e)}"
            )
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif request.method == "PATCH":
        logger.info(f"Profile update request | user={user_id}")

        try:
            serializer = UserProfileSerializer(
                user,
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                updated_fields = list(request.data.keys())

                serializer.save()

                logger.info(
                    f"Profile updated | user={user_id} | fields={updated_fields}"
                )

                return Response(serializer.data)

            logger.warning(
                f"Profile update validation failed | user={user_id} | errors={serializer.errors}"
            )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.exception(
                f"Error updating profile | user={user_id} | error={str(e)}"
            )
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )