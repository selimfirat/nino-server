from django.db import models
from django.core.validators import RegexValidator



class User(models.Model):
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    created = models.DateTimeField(auto_now_add=True)
    name = models.TextField(unique=False, max_length=15)
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=False, unique=True) # validators should be a list
    last_verification_code = models.TextField(blank=True)