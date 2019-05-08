import pke
from nltk.corpus import stopwords

class KeyPhraseExtractor:
    
    def get_keyphrases(self, text):
        try:
            return _get_keyphrases(text)
        except:
            return []

    def _get_keyphrases(self, text):
        if len(text.replace("\s", "")) == 0:
            return []
        # 1. create a YAKE extractor.
        extractor = pke.unsupervised.YAKE()

        # 2. load the content of the document.
        extractor.load_document(input=text,
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
        keyphrases_res = extractor.get_n_best(n=5, threshold=threshold)

        keyphrases = []
        for kp, score in keyphrases_res:
            keyphrases.append({
                "keyphrase": kp,
                "score": score
            })
            
        return keyphrases