import os
import sys
import base64
import requests
import json
import re

# import cv2

# later read from config file
app = "ata_aydin_ug_bilkent_edu_tr"
key = "b60b9fd4c8e538eb667f"
headers = {"app_id": app, "app_key": key, "Content-type": "application/json"}
# headers = {"app_id": app, "app_key": key, "Content-type": "application/json", "ocr": ["math", "text"]}

class MathpixRepository:
    def __init__(self, app=app, key=key):
        if app is None:
            if 'MATHPIX_APP_ID' in os.environ:
                app = os.environ['MATHPIX_APP_ID']

            if 'MATHPIX_APP_KEY' in os.environ:
                key = os.environ['MATHPIX_APP_KEY']
        if app is None or key is None:
            raise
        
        self.headers = headers
        
    def process_image(self, img_path, jres):
        '''
        Receives image of note and output of layout analysis, sends each box to Mathpix server, and returns output to each box.

        Inputs:
        img_path: path to image
        jres: tuple (lines, images, paragraphs), elements themselves lists of dicts {[text,] left, top, right, bottom}

        Output: (lines, images, paragraphs, equations, tables, figures)
        equations: list of dicts {text, latex, conf, left, top, right, bottom}
        tables: list of dicts {text, latex, conf, left, top, right, bottom}
        figures: list of dicts {type, left, top, right, bottom}, type in {'chart', 'graph', 'diagram'}
        '''
        lines, images, paragraphs = jres
        equations, tables, figures = [], [], []
        # img = cv2.imread(img_path)
        
        reg = re.compile(r'\\\((.*?)\\\)')
        
        # check lines
        textlines = [] # list of lines comprised only of text
        for line in lines:
            # crop image
            x0, y0, x1, y1 = line['left'], line['bottom'], line['right'], line['top']
            # cropped = img[y0:y1, x0:x1]

            # send request (may later do these in batch)
            r = self.query(img_path, False, region=(x0,y0,x1,y1))
            
            # detect if equation in line, whether from confidence value or analyzing latex output
            
            # if equation detected, add it to list
            if not r['error']:
                # text = r['latex_styled'] if 'latex_styled' in r else r['latex_normal']
                text = r['text']
                segs = reg.split(text)
                if len(segs) == 1: # text does not contain equation
                    textlines.append(line)
                    continue
                text = '$'.join(segs) # possibly first analyze latex segments, align text to text in line etc.
                segs[::2] = ['\\text{'+s+'}' if s else '' for s in segs[::2]] # bracket each text segment
                latex = ''.join(segs)
                
                conf = r['latex_confidence_rate'] # set thresholds perhaps
                
                equations.append({'text':text, 'latex':latex, 'conf':conf, 'left':x0, 'bottom':y0, 'right':x1, 'top':y1})
            else:
                textlines.append(line)
        
        # check images
        for rect in images:
            # crop image
            x0, y0, x1, y1 = rect['left'], rect['bottom'], rect['right'], rect['top']
            # cropped = img[y0:y1, x0:x1]

            # send request (may later do these in batch)
            r = self.query(img_path, False, region=(x0,y0,x1,y1))

            # identify type
            if 'contains_graph' in r['detection_list']:
                typ = 'graph'
            elif 'contains_chart' in r['detection_list']:
                typ = 'chart'
            elif 'contains_diagram' in r['detection_list']:
                typ = 'diagram'
            elif 'contains_table' in r['detection_list'] and not r['error']:
                text = r['latex_styled'] if 'latex_styled' in r else r['latex_normal']
                conf = r['latex_confidence_rate']
                
                # may use bounding box returned in r['position'] to fine tune coordinates
                tables.append({'latex':text, 'conf':conf, 'left':x0, 'bottom':y0, 'right':x1, 'top':y1})
                continue
            elif 'is_not_math' not in r['detection_list'] and not r['error']: # equation in standalone figure
                text = r['latex_styled'] if 'latex_styled' in r else r['latex_normal'] # possibly analyze for text vs. eqn
                conf = r['latex_confidence_rate']
                
                # may use bounding box returned in r['position'] to fine tune coordinates
                equations.append({'latex':text, 'conf':conf, 'left':x0, 'bottom':y0, 'right':x1, 'top':y1})
                continue
            else: # may also check is_blank etc.
                continue

            figures.append({'type':typ, 'left':x0, 'bottom':y0, 'right':x1, 'top':y1})
            
            
        # return lines, images, paragraphs, equations, tables, figures
        return textlines, images, paragraphs, equations, tables, figures
    
    def latex2image(self, latex, ext='png', size='large'):
        'Convert latex to image'
        url = 'https://latex.codecogs.com/%s.latex?\%s%s' % (ext, size, latex.replace(' ', '&space;'))
        try:
            r = requests.get(url)
            if r.status_code != requests.codes.ok:
                return None
            return r.content
        except:
            return None
        
    def query(self, file_path, output=True, img=None, region=None):
        'Query server for single image'
        
        if img is not None:
            imgbin = cv2.imencode('.jpg', img)[1]
        else:
            imgbin = open(file_path, "rb").read()
        image_uri = "data:image/jpg;base64," + base64.b64encode(imgbin).decode()
        data = {'src': image_uri, 'formats': ['latex_normal', 'latex_styled', 'text']}
        if region:
            x0, y0, x1, y1 = region
            data['region'] = {'top_left_x': x0, 'top_left_y': y0, 'width': x1-x0, 'height': y1-y0}
        r = requests.post("https://api.mathpix.com/v3/latex",
                          data=json.dumps(data), headers=self.headers)
        if not output:
            return json.loads(r.text)
        return json.dumps(json.loads(r.text), indent=4, sort_keys=True)


