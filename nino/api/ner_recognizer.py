import anago
from anago.utils import download, load_data_and_labels
from flair.data import Sentence
import nltk
from flair.data import Sentence
from flair.models import SequenceTagger

class NERRecognizer:
    
    def __init__(self):
        self.ontoner_tagger = SequenceTagger.load('ner-ontonotes-fast') 

    def get_ner_entities(self, text):
        entities = []
        
        try:
            sentences = nltk.sent_tokenize(text)
        except:
            sentences = [text]
        
        print(sentences)
        
        for sent in sentences:
            sentence = Sentence(sent)
            self.ontoner_tagger.predict(sentence)
            sent_tags = sentence.to_dict(tag_type='ner')
            entities.extend(sent_tags["entities"])

        return entities