from django.contrib.auth.models import AbstractBaseUser, BaseUserManager 
from django.db import models 
from cloudinary.models import CloudinaryField



class UserManager(BaseUserManager):
    def create_user(self, email, password=None): 
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email) 
        user = self.model(email=email) 
        user.set_password(password) 
        user.save(using=self._db) 
        return user 
 
    def create_superuser(self, email, password): 
        user = self.create_user(email, password) 
        user.is_admin = True 
        User.is_superuser = True # type: ignore
        user.save(using=self._db) 
        return user 
 
class User(AbstractBaseUser): 
    email = models.EmailField(unique=True) 
    name = models.CharField(max_length =255) 
    is_active = models.BooleanField(default=True) 
    is_admin = models.BooleanField(default=False) 
    image = models.FileField(upload_to='user_profile_pic/',null=True,blank=True)
    objects = UserManager() 
 
    USERNAME_FIELD = 'email'

class Recipe(models.Model):
    choices = (
        ('Easy','Easy'),
        ('Medium','Medium'),
        ('Hard','Hard')
    )
    user = models.ForeignKey("User",on_delete=models.CASCADE)
    title = models.CharField(max_length=25)
    ingredients = models.TextField()
    steps = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)
    cooking_time = models.CharField(max_length=20)
    difficulty_level = models.CharField(choices=choices,max_length=10)
    image = CloudinaryField('image', null=True, blank=True)

class WishList(models.Model):
    user = models.ForeignKey("User",on_delete=models.CASCADE)
    recipe = models.ForeignKey("Recipe",on_delete=models.CASCADE)