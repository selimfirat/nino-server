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
from .gcloud import GCloudRepository
from .mathpix import MathpixRepository

from rest_framework.decorators import api_view
from rest_framework.response import Response

ner = NERRecognizer()
keyphrase_extractor = KeyPhraseExtractor()
abbyy = AbbyyRepository("nino_batu", "nRYRO0U1yeElxbzvSxHNKYW4")
wikifier = Wikifier()
mpix = MathpixRepository()
gcloud = GCloudRepository()




@api_view(['POST'])
def text_analysis(request):
    request_dict = dict(request.data)
    
    text = request_dict["text"]
    
    keyphrases = keyphrase_extractor.get_keyphrases(text)

    for kp in keyphrases:
        kp["info"] = wikifier.get_entity_info(kp["keyphrase"])

    res = {}
    res["keyphrases"] = keyphrases

    res["entities"] = ner.get_ner_entities(text)

    res["entitylist"] = []
    
    for kp in res["keyphrases"]:
        res["entitylist"].append(kp["keyphrase"].title())
    
    for e in res["entities"]:
        res["entitylist"].append(e["text"].title())
    
    res["entitylist"] = list(set(res["entitylist"]))
    
    return Response(res)


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
        
        print(req.__dict__)
        
        request_dict = dict(request.data)

        initial_image_str = request_dict['image'][0]._get_name()
        # username = req.__dict__['data']['owner'] #str(request.user)
        request_id = str(req.__dict__['data']['id'])
        # print('Running request for user ' + username + " with request id #" + request_id)
        dir_notes = "notes/"

        image_path = dir_notes + 'original_images/' + initial_image_str.replace(" ", "_")
        lines, images, paragraphs = abbyy.process_image(source_image_path=image_path)
        
        lines, images, paragraphs, equations, tables, figures = mpix.process_image(img_path=image_path, jres=(lines, images, paragraphs))

        images = gcloud.append_image_labels(image_path, images)


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