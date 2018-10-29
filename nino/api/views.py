import hashlib

import time
from django.shortcuts import render
from rest_framework import viewsets, mixins, generics, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from nino.api.models import User, Note, Category
from nino.api.serializers import UserSerializer, NoteSerializer, CategorySerializer


class NoteList(generics.ListCreateAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class NoteDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

class CategoryList(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class UserSendVerificationCodeView(APIView):

    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.phone_exists(serializer.validated_data["phone_number"]):
                user = User.objects.get(phone_number=serializer.validated_data["phone_number"])
                serializer = UserSerializer(user, serializer)

            serializer.validated_data["verification_code"] = hashlib.shake_256(str(time.time()).encode("utf-8")).hexdigest(length=6).upper()
            # TODO: send verification code as SMS

            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserVerifyCodeView(APIView):

    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)

        if serializer.verify_code(phone_number=serializer.initial_data["phone_number"], verification_code=serializer.initial_data["verification_code"]):
            user = User.objects.get(phone_number=serializer.initial_data["phone_number"])
            token = Token.objects.create(user=user)
            return Response(dict(auth_token=token.key), status=status.HTTP_200_OK)


        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)