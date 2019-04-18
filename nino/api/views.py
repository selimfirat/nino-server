from rest_framework import status, permissions
from rest_framework import mixins, generics
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from .models import Note
from .serializers import NoteSerializer
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

import base64

from .wikifier import Wikifier

from .keyphrase_extractor import KeyPhraseExtractor
from .ner_recognizer import NERRecognizer
from PIL import Image
import pathlib


from .abbyy_repository import AbbyyRepository
# Temporarily disabled due to dependencies
# from .mathpix import MathpixRepository
# mpix = MathpixRepository()

# GCloud: Disabled due to dependencies
# from .gcloud import GCloudRepository


class NoteList(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     generics.GenericAPIView):
    """
     List all notes, or create a note
    """
    permission_classes = ()
    parser_classes = (JSONParser, MultiPartParser, FormParser,)

    serializer_class = NoteSerializer

    def get_queryset(self, *args, **kwargs):
        return Note.objects.all()

    def perform_create(self, serializer):
        serializer.save()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        req = self.create(request, *args, **kwargs)
        ner = NERRecognizer()

        keyphrase_extractor = KeyPhraseExtractor()

        abby = AbbyyRepository("testsdaads", "13JgRczOS+nmjkn80ewUwXxl")
        wikifier = Wikifier()

        
        print(req.__dict__)
        
        request_dict = dict(request.data)
        print(req.__dict__['data']['id'])
        initial_image_str = request_dict['image'][0]._get_name()
        # username = req.__dict__['data']['owner'] #str(request.user)
        request_id = str(req.__dict__['data']['id'])
        # print('Running request for user ' + username + " with request id #" + request_id)
        dir_notes = "notes/"

        image_path = dir_notes + 'original_images/' + initial_image_str.replace(" ", "_")
        lines, images, paragraphs = abby.process_image(source_image_path=image_path)
        
        # Temporarily disabled due to dependencies
        # lines, images, paragraphs, equations, tables, figures = mpix.process_image(img_path=image_path, jres=(lines, images, paragraphs))

        # GCloud: Disabled due to dependencies
        # gcloud = GCloudRepository()
        # lines, paragraphs, bounds = gcloud.process_document(image_path) # Can process a crop of the image if given bottom,top, left, right vertices
        #
        # TODO: Should choose between GCloud or Abbyy according to confidence
        #
        # images_with_labels = []
        # for image in images:
        #     labels = gcloud.get_image_labels(image_path, image.bottom, image.top, image.left, image.right)
        #     images_with_labels.append([image, labels])

        req.__dict__['data']['lines'] = lines
        req.__dict__['data']['images'] = images
        req.__dict__['data']['paragraphs'] = paragraphs
        
        # Temporarily disabled due to dependencies
        """
        req.__dict__['data']['equations'] = equations
        req.__dict__['data']['tables'] = tables
        req.__dict__['data']['figures'] = figures
        """
        
        all_text = "\n".join([par["text"] for par in paragraphs])
        

        keyphrases = keyphrase_extractor.get_keyphrases(all_text)
        
        for kp in keyphrases:
            kp["info"] = wikifier.get_entity_info(kp["keyphrase"])
        
        req.__dict__["data"]["keyphrases"] = keyphrases
        
        req.__dict__["data"]["entities"] = ner.get_ner_entities(all_text)
        
        return req

class NoteDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    """
    Retrieve, update or delete a note instance.
    """
    permission_classes = ()
    serializer_class = NoteSerializer

    def get_object(self, pk):
        try:
            return Note.objects.get(pk=pk)
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
