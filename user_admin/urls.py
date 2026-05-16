from django.urls import path
from user_admin import views

urlpatterns = [
    path("admin_login/",views.admin_login),
    path("listuser",views.list_users),
    path("togglestatus/<int:pk>",views.toggle_block_state),
    path("listrecipe/<int:pk>",views.user_recipes),
    path("recipedetail/<int:pk>",views.recipe_view),
    path("logout",views.admin_logout),
    path("deleterecipe/<int:pk>",views.recipe_delete)
]