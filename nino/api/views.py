from rest_framework import status, permissions
from rest_framework import mixins, generics
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from .models import Note
from .serializers import NoteSerializer
from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)

from .pipeline.nino_object import NinoObject
from .pipeline.nino_utils import *
#from .pipeline.RequestHandleThread import RequestHandleThread
from .pipeline.nino_pipeline import NinoPipeline
from .pipeline import M

from PIL import Image
import pathlib


dir_notes = "notes/"
class NoteList(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     generics.GenericAPIView):
    """
     List all notes, or create a note
    """
    permission_classes = (permissions.IsAuthenticated, )
    parser_classes = (JSONParser, MultiPartParser, FormParser,)

    serializer_class = NoteSerializer

    def get_queryset(self, *args, **kwargs):
        return Note.objects.all().filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        req = self.create(request, *args, **kwargs)
        load_modules()
        crs = get_class_references()
        
        print(req.__dict__)
        
        request_dict = dict(request.data)
        print(req.__dict__['data']['id'])
        initial_image_str = request_dict['image'][0]._get_name()
        username = req.__dict__['data']['owner'] #str(request.user)
        request_id = str(req.__dict__['data']['id'])
        print('Running request for user ' + username +
        " with request id #" + request_id)

        initial_image = Image.open(dir_notes + 'original_images/' + initial_image_str)

        modules = [
            crs[M.LAYOUT_ANALYSIS]()
            #crs[M.PREPROCESS](),
            #crs[M.REGION_SEGMENTATION]("param1", "param2")
        ]
        
        # Create NinoObject with a name and initial image
        no = NinoObject(request_id, initial_image) # Temp solution for com

        # Create NinoPipeline with modules and NinoObject
        np = NinoPipeline(no, modules)
        np.run() # Start processsing

        ########################################################################
        # For debuging purposes
        ########################################################################
        path_request = dir_notes + 'processed_images/' + request_id + '/'
        pathlib.Path(path_request).mkdir(parents=True, exist_ok=True)
        for m in modules:
            output_of_module = no.get(m.process_name)
            output_of_module.save(path_request + m.process_name + ".jpg", "JPEG")
        final_out = no.get_final_out()
        final_out.save(path_request + "FINAL.jpg", "JPEG")
        ########################################################################

        print("Done processing!")
        print("done")
        
        import base64
        
        with open(path_request + "FINAL.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            req.__dict__['data']['image'] = encoded_string
            
        return req

class NoteDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    """
    Retrieve, update or delete a note instance.
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = NoteSerializer

    def get_object(self, pk):
        try:
            return Note.objects.filter(owner=self.request.user).get(pk=pk)
        except Note.DoesNotExist:
            raise

    def get(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = NoteSerializer(snippet)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        note = self.get_object(pk)
        serializer = NoteSerializer(note, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        note = self.get_object(pk)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
