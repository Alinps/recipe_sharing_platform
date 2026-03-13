from django.contrib import admin
from django.urls import path,include
from app import views

urlpatterns = [
    path('signup/',views.Signup,name="signup"),
    path('login/',views.login,name="login")
]