from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from django.contrib.auth.models import BaseUserManager
from django.utils import timezone


class CustomUserManager(BaseUserManager):

    def _create_user(self, phone_number, password,
                     is_staff, is_superuser, **extra_fields):

        if not phone_number:
            raise ValueError('The given phone must be set')


        user = self.model(phone_number=phone_number,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        return self._create_user(phone_number, password, False, False,
                                 **extra_fields)

    def create_superuser(self, phone_number, password, **extra_fields):
        return self._create_user(phone_number, password, True, True,
                                 **extra_fields)


class User(AbstractBaseUser):
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    created = models.DateTimeField(auto_now_add=True)
    name = models.TextField(unique=False, max_length=24, blank=True)
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=False, unique=True) # validators should be a list
    verification_code = models.CharField(blank=True, max_length=12)
    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'

    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

class Category(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    name = models.TextField(max_length=200)
    class Meta:
        ordering = ('name',)

class Note(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    title = models.TextField(unique=False, max_length=100)

    class Meta:
        ordering = ('created',)
