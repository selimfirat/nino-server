from rest_framework import serializers
from .models import Note
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    notes = serializers.PrimaryKeyRelatedField(many=True, queryset=Note.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'notes')

class NoteSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Note
        fields = ('id', "owner", 'name', 'image')
