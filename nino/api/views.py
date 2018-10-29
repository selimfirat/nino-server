from rest_framework import status, permissions
from rest_framework import mixins, generics
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from .models import Note
from .serializers import NoteSerializer, UserSerializer
from django.contrib.auth.models import User
from rest_framework import permissions
from .permissions import IsOwnerOrReadOnly

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class NoteList(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     generics.GenericAPIView):
    """
     List all notes, or create a note
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    parser_classes = (JSONParser, MultiPartParser, FormParser,)

    serializer_class = NoteSerializer

    def get_queryset(self, *args, **kwargs):
        return Note.objects.all().filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
