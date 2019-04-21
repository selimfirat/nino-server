import anago
from anago.utils import download, load_data_and_labels
from flair.data import Sentence
import nltk
from flair.data import Sentence
from flair.models import SequenceTagger

class NERRecognizer:
    
    def __init__(self):
        # ner_url = 'https://storage.googleapis.com/chakki/datasets/public/ner/model_en.zip'
        self.ner_tagger = SequenceTagger.load('ner')
        self.ontoner_tagger = SequenceTagger.load('ner-ontonotes')

        # download(ner_url)
        # self.ner_model = anago.Sequence.load('/home/yilmazselimfirat3/.keras/datasets/weights.h5', '/home/yilmazselimfirat3/.keras/datasets/params.json', '/home/yilmazselimfirat3/.keras/datasets/preprocessor.pickle')  


    def get_ner_entities(self, text):
        entities = []
        sentences = nltk.sent_tokenize(text)
        for sent in sentences:
            sentence = Sentence(sent)
            self.tagger.predict(sentence)
            sent_tags = sentence.to_dict(tag_type='ner')
            entities.extend(sent_tags["entities"])

            self.ontoner_tagger.predict(sentence)
            sent_tags = sentence.to_dict(tag_type='ner-ontonotes')
            entities.extend(sent_tags["entities"])

        return entities