from django.contrib import admin
from django.urls import path,include
from app import views

urlpatterns = [
    path('signup/',views.Signup,name="signup"),
    path('login_user/',views.Login_user,name="login"),
    path('logout/',views.logout_view,name="logout"),
    path('create/',views.create_recipe,name="create"),
    path('list/',views.list_recipe,name="list"),
    path('recipedetails/<int:pk>',views.recipe_details,name="recipe_details"),
    path('delete_recepi/<int:pk>',views.delete_recipe,name="delete"),
    path('search/',views.recipe_search,name="search"),
    path('passwordchange/',views.password_change,name="password_change"),
    path('update/',views.edit_recipe,name="edit"),
    path("chat/", views.chatbot,name="chatbot"),
    path("profile/<int:user_id>/",views.user_profile,name="user_profile"),
    path("profile/<int:user_id>/wishlist/", views.user_wishlist),
    path('wishlist/toggle/', views.toggle_wishlist),
     
]