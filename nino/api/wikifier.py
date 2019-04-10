import requests

class Wikifier:
    
    def get_entity_info(self, phrase):
                
        res = requests.get('https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exintro&explaintext&redirects=1&titles=' + phrase).json()
        
        
        page = list(res["query"]["pages"].items())[0]
        
        page_id = int(page[0])        
        
        if page_id == -1:
            return None

        description = page[1]["extract"]
        
        wiki_url = "http://en.wikipedia.org/?curid=" + str(page_id)
        
        return {
            "wiki_url": wiki_url,
            "description": description
        }