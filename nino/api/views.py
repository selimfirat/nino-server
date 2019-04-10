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

import base64
import pke
from nltk.corpus import stopwords
import anago
from anago.utils import download, load_data_and_labels
from .wikifier import Wikifier

from PIL import Image
import pathlib

from .abbyy_repository import AbbyyRepository
# Temporarily disabled due to dependencies
# from .mathpix import MathpixRepository
# mpix = MathpixRepository()

        
ner_url = 'https://s3-ap-northeast-1.amazonaws.com/dev.tech-sketch.jp/chakki/public/conll2003_en.zip'

weights, params, preprocessor = download(ner_url)
ner_model = anago.Sequence.load(weights, params, preprocessor)

dir_notes = "notes/"
abby = AbbyyRepository("testsdaads", "13JgRczOS+nmjkn80ewUwXxl")
wikifier = Wikifier()

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
        
        print(req.__dict__)
        
        request_dict = dict(request.data)
        print(req.__dict__['data']['id'])
        initial_image_str = request_dict['image'][0]._get_name()
        username = req.__dict__['data']['owner'] #str(request.user)
        request_id = str(req.__dict__['data']['id'])
        print('Running request for user ' + username +
        " with request id #" + request_id)

        image_path = dir_notes + 'original_images/' + initial_image_str
        lines, images, paragraphs = abby.process_image(source_image_path=image_path)
        
        # Temporarily disabled due to dependencies
        # lines, images, paragraphs, equations, tables, figures = mpix.process_image(img_path=image_path, jres=(lines, images, paragraphs))

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

        # 1. create a YAKE extractor.
        extractor = pke.unsupervised.YAKE()

        # 2. load the content of the document.
        extractor.load_document(input=all_text,
                                language='en',
                                normalization=None)


        # 3. select {1-3}-grams not containing punctuation marks and not
        #    beginning/ending with a stopword as candidates.
        stoplist = stopwords.words('english')
        extractor.candidate_selection(n=3, stoplist=stoplist)

        # 4. weight the candidates using YAKE weighting scheme, a window (in
        #    words) for computing left/right contexts can be specified.
        window = 2
        use_stems = False # use stems instead of words for weighting
        extractor.candidate_weighting(window=window,
                                      stoplist=stoplist,
                                      use_stems=use_stems)

        # 5. get the 10-highest scored candidates as keyphrases.
        #    redundant keyphrases are removed from the output using levenshtein
        #    distance and a threshold.
        threshold = 0.8
        keyphrases_res = extractor.get_n_best(n=10, threshold=threshold)

        
        keyphrases = []
        for keyphrase, score in keyphrases_res:
            keyphrase_dict = {
                "keyphrase": keyphrase,
                "score": score,
                "info": wikifier.get_entity_info(keyphrase)
            }
            
            keyphrases.append(keyphrase_dict)


        req.__dict__["data"]["keyphrases"] = keyphrases
        
        
        entities = []
        # entities = ner_model.analyze(all_text)["entities"]

        req.__dict__["data"]["entities"] = entities
        
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
