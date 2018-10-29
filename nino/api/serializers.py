from django.core.validators import RegexValidator
from rest_framework import serializers
from nino.api.models import Category, Note, User


class UserSerializer(serializers.ModelSerializer):

    def phone_exists(self, phone_number):
         return self.Meta.model.objects.filter(phone_number=phone_number).exists()

    def verify_code(self, phone_number, verification_code):
        return self.Meta.model.objects.filter(phone_number=phone_number, verification_code=verification_code).exists()

    class Meta:
        model = User
        fields = ("id", 'created', 'name', 'phone_number', "verification_code")

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("created", "name")

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ("created", "title")