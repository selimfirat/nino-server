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
import subprocess
import base64
import re
from .wikifier import Wikifier
from .question_generator import QuestionGenerator

from .keyphrase_extractor import KeyPhraseExtractor
from .ner_recognizer import NERRecognizer
from PIL import Image
import pathlib

import re
from .abbyy_repository import AbbyyRepository
from .gcloud import GCloudRepository
from .mathpix import MathpixRepository
from .export import PDFExporter

from rest_framework.decorators import api_view
from rest_framework.response import Response

ner = NERRecognizer()
keyphrase_extractor = KeyPhraseExtractor()
abbyy = AbbyyRepository("ORGRIMMAR", "rup4XXa5j7dF419iuT4dp7C+")
wikifier = Wikifier()
# mpix = MathpixRepository()
# gcloud = GCloudRepository()
question_generator = QuestionGenerator()
pdfexp = PDFExporter()


@api_view(['POST'])
def analyze_text(request):
    request_dict = dict(request.data)
    text = "".join(request_dict["text"])
    print("printing text:", text)
    text = text.replace(".", " . ")
    text = text.replace("\n", " . ")
    text = re.sub("[^a-zA-Z0-9_\s\.]", "", text)
    text = re.sub(' +', ' ', text)
    
    
    keyphrases = keyphrase_extractor.get_keyphrases(text)
    ner_entities = ner.get_ner_entities(text)
    
    entities = ner_entities + keyphrases
    
    entities.sort(key=lambda x: -len(x))
    
    entitylist = []
    
    for entity in entities:
        e = entity["text"]
        if not any(e in ex for ex in entitylist):
            entitylist.append(e)
    
    res = {
        "entitylist": entitylist,
    }
    
    return Response(res)


@api_view(['POST'])
def analyze_text_questions(request):
    request_dict = dict(request.data)
    text = "".join(request_dict["text"])
    print("printing text:", text)
    text = text.replace(".", " . ")
    text = text.replace("\n", " . ")
    text = re.sub("[^a-zA-Z0-9_\s\.]", "", text)
    text = re.sub(' +', ' ', text)
    
    
    keyphrases = keyphrase_extractor.get_keyphrases(text)
    ner_entities = ner.get_ner_entities(text)
    
    entities = ner_entities + keyphrases
    
    entities.sort(key=lambda x: -len(x))
    
    entitylist = []
    
    for entity in entities:
        e = entity["text"]
        if not any(e in ex for ex in entitylist):
            entitylist.append(e)

    
    questions = question_generator.generate_questions(text, entitylist)
    
    res = {
        "entitylist": entitylist,
        "questions": questions
    }
    
    return Response(res)


@api_view(["POST"])
def generate_questions(request):
    request_dict = dict(request.data)
    text = request_dict["text"]
    
    res = question_generator.generate_questions(text)
    
    return Response(res)

@api_view(['POST'])
def export_pdf(request):
    def read_file(fname):
        with open(fname, 'rb') as f:
            res = f.read()
        return res
    request_dict = dict(request.data)
    # text = request_dict['text']
    fname = 'notes/export/temp' # TODO later use name of file
    
    pdfexp.export(request_dict, fname)
    
    res = {
        'latex': read_file(fname + '.tex'),
        'pdf':   read_file(fname + '.pdf')
    }
    
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
        page, lines, images, paragraphs = abbyy.process_image(source_image_path=image_path)
        
        # lines, images, paragraphs, equations, tables, figures = mpix.process_image(img_path=image_path, jres=(lines, images, paragraphs))

        # images = gcloud.append_image_labels(image_path, images)


        # req.__dict__['data']['lines'] = lines
        req.__dict__["data"]["page"] = page
        req.__dict__['data']['images'] = images
        req.__dict__['data']['paragraphs'] = paragraphs

        # req.__dict__['data']['equations'] = equations
        # req.__dict__['data']['tables'] = tables
        # req.__dict__['data']['figures'] = figures
        
        # all_text = "\n".join([par["text"] for par in paragraphs])
        
        return req