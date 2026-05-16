from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from django.db.models import Q
from app.models import User
from app.models import Recipe
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND,HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework import status
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from app.utils.pagination import RecipePagination
from .serializers import UserListSerializer,RecipeListSerializer, RecipeDetailSerializer
import logging

logger = logging.getLogger("recipe_app")

@api_view(["POST"])
@permission_classes((AllowAny,))

def admin_login(request):

    email = request.data.get("email")
    password = request.data.get("password")

    masked_email = email[:3] + "***" if  email else "unknown"
    logger.info(f"Login attempt | email={masked_email}")
    
    try:
        if email is None or password is None:

            logger.warning(f"Login failed | reason=missing_credentials | email={masked_email}")
            return Response(
                {"error":"All fields are required"},
                status=HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(email=email,password=password)

        if not user:
            logger.warning(f"Login failed | reason=invalid_credentials | email={masked_email}")
            return Response(
                {"error":"Unauthorized access. Invalid credentials."},
                status=HTTP_400_BAD_REQUEST
            )
        
        if not user.is_admin: # type: ignore
            logger.warning(f"Login failed | reason=unauthorized access | email={masked_email}")
            return Response(
                {"error":"Access denied. You do not have administrator privileges."}
            )

        token, _ = Token.objects.get_or_create(user=user)

        logger.info(f"Login successful | user={user.id}") # type: ignore

        return Response(
            {
                "token":token.key,
                "admin":{
                    "id":user.id, # type: ignore
                    "name":user.name  # type: ignore
                }
                
                },status=HTTP_200_OK
        )
    except Exception as e:
        logger.exception(
            f"Login error | email={masked_email} | error={str(e)}"
        )
        return Response(
            {"error":"Something went wrong"},status=HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(["POST"])
@permission_classes([IsAuthenticated])

def admin_logout(request):

    user = request.user.id
    logger.info(f"Logout attempt | user={user}")

    try:
        request.user.auth_token.delete()
        logger.info(f"Logout successfull | user={user}")
        return Response(
            {"message":"Logged out successfully"},status=status.HTTP_200_OK
        )
    except Exception as e:

        logger.exception(
            f"Logout failed | user={user} | error={str(e)}"
        )
        return Response(
            {"error":"Logout failed"},
            status=status.HTTP_400_BAD_REQUEST
        )



@api_view(["GET"])
@permission_classes([IsAuthenticated])

def list_users(request):
    """
    View to list users with optimized searching and strict permissions.
    """
    user = request.user

    logger.info(
        f"List users attempt | admin={user.id}"
    )

    search = request.GET.get("search","").strip()

    if not user.is_admin:
        logger.warning(f"Unauthorized user list access | reason=unauthorized access | user={user.id}")
        return Response(
                {"error":"Access denied. You do not have administrator privileges."},
                status=status.HTTP_403_FORBIDDEN
            )

    queryset = User.objects.only("id","email","name","is_active","image","created_at").order_by("id")

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search)
        )

    paginator = RecipePagination()
    paginated_queryset = paginator.paginate_queryset(queryset,request)
    serializer = UserListSerializer(paginated_queryset,many=True)

    logger.info(
        f"Users fetched | returned = {len(serializer.data)}"
    )

    return paginator.get_paginated_response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def toggle_block_state(request,pk):

    admin = request.user

    logger.info(f"Toggle user status attempt | admin={admin.id} | target_user={pk}")

    if not admin.is_admin:

        logger.warning(f"Permission denied | user={admin.id}")

        return Response(
                {"error":"Access denied. You do not have administrator privileges."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    
    user = get_object_or_404(User, id=pk)
    
    if user.id == admin.id: # type: ignore

        logger.warning(f"Self block attempt | user={admin.id}")
        return Response(
            {"error":"You cannot block your own account."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    logger.info(
        f"User status updated | admin={admin.id}"
        f"| targer_user={user.id}" # type: ignore
        f"| is_active={user.is_active}"
    )

    return Response(
        {
            "message": (
                "User unblocked successfully."
                if user.is_active
                else "User blocked successfully"
            ),
            "user_id":user.id, # type: ignore
            "is_active":user.is_active
        },
        status=HTTP_200_OK
    )




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_recipes(request,pk):
    
    admin = request.user

    logger.info(
        f"List user recipes request | target_user={pk}"
    )

    search = request.GET.get("search","").strip()

    if not admin.is_admin:

        logger.warning(f"Permission denied | user={admin.id}")

        return Response(
                {"error":"Access denied. You do not have administrator privileges."},
                status=status.HTTP_403_FORBIDDEN
            )
    user = get_object_or_404(User,id=pk)
    
    queryset = (
        Recipe.objects
        .filter(user=user)
        .select_related("user")
        .only(
            "id",
            "title",
            "image",
            "created_at",
            "user__name",
        )
        .order_by("-created_at")
    )

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)|
            Q(ingredients__icontains=search)
        )

    paginator = RecipePagination()
    paginated_queryset = paginator.paginate_queryset(queryset,request)

    serializer  = RecipeListSerializer(paginated_queryset,many=True)

    logger.info(
        f"User recipes fetched | user={pk} "
        f"| returned={len(serializer.data)}"
    )

    return paginator.get_paginated_response(
        serializer.data
    )



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recipe_view(request,pk):

    admin = request.user

    if not admin.is_admin:

        logger.warning(f"Permission denied | user={admin.id}")
        return Response(
                {"error":"Access denied. You do not have administrator privileges."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    recipe = get_object_or_404(Recipe,id=pk)

    serializer = RecipeDetailSerializer(recipe)

    logger.info(
        f"Recipe detail fetched | user={pk} "
    )

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def recipe_delete(request,pk):

    admin = request.user

    if not admin.is_admin:

        logger.warning(f"Permission denied | user={admin.id}")
        return Response(
                {"error":"Access denied. You do not have administrator privileges."},
                status=status.HTTP_403_FORBIDDEN
            )

    recipe = get_object_or_404(Recipe,id=pk) 

    recipe.delete()

    return Response(
        {"message":"Recipe deleted successfully"}
    , status=status.HTTP_200_OK)






    
   

       


