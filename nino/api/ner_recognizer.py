import anago
from anago.utils import download, load_data_and_labels

class NERRecognizer:
    
    def __init__(self):
        # ner_url = 'https://storage.googleapis.com/chakki/datasets/public/ner/model_en.zip'

        # download(ner_url)
        self.ner_model = anago.Sequence.load('/home/yilmazselimfirat3/.keras/datasets/weights.h5', '/home/yilmazselimfirat3/.keras/datasets/params.json', '/home/yilmazselimfirat3/.keras/datasets/preprocessor.pickle')  


    def get_ner_entities(self, text):
        
        return self.ner_model.analyze(text)["entities"]