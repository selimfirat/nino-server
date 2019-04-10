#!/usr/bin/env python
import os
import sys
import base64
import requests
import json

import cv2

# later read from config file
app = "ata_aydin_ug_bilkent_edu_tr"
key = "b60b9fd4c8e538eb667f"
headers = {"app_id": app, "app_key": key, "Content-type": "application/json"}

class MathpixRepository:
    def __init__(self, app=app, key=key):
        if app is None:
            if 'MATHPIX_APP_ID' in os.environ:
                app = os.environ['MATHPIX_APP_ID']

            if 'MATHPIX_APP_KEY' in os.environ:
                key = os.environ['MATHPIX_APP_KEY']
        if app is None or key is None:
            raise
        
        self.headers = {"app_id": app, "app_key": key, "Content-type": "application/json"}
        
    def process_image(self, img_path, jres):
        '''
        Receives image of note and output of layout analysis, sends each box to Mathpix server, and returns output to each box.

        Inputs:
        img_path: path to image
        jres: tuple (lines, images, paragraphs), elements themselves lists of dicts {[text,] left, top, right, bottom}

        Output: (lines, images, paragraphs, equations, tables, figures)
        equations: list of dicts {latex, conf, left, top, right, bottom}
        tables: list of dicts {latex, conf, left, top, right, bottom}
        figures: list of dicts {type, left, top, right, bottom}, type in {'chart', 'graph', 'diagram'}
        '''
        lines, images, paragraphs = jres
        equations, tables, figures = [], [], []
        img = cv2.imread(img_path)
        
        # check lines
        for line in lines:
            # crop image
            x0, y0, x1, y1 = line['left'], line['top'], line['right'], line['bottom']
            cropped = img[y0:y1, x0:x1]

            # send request (may later do these in batch)
            r = self.query(img_path, False, cropped)
            
            # TODO detect if equation in line, whether from confidence value or analyzing latex output
            
            # if equation detected, add it to list
            if not r['error']:
                text = r['latex_styled'] if 'latex_styled' in r else r['latex_normal']
                conf = r['latex_confidence_rate']
                
                equations.append({'latex':text, 'conf':conf, 'left':x0, 'top':y0, 'right':x1, 'bottom':y1})
        
        # check images
        for rect in images:
            # crop image
            x0, y0, x1, y1 = rect['left'], rect['top'], rect['right'], rect['bottom']
            cropped = img[y0:y1, x0:x1]

            # send request (may later do these in batch)
            r = self.query(img_path, False, cropped)

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
                tables.append({'latex':text, 'conf':conf, 'left':x0, 'top':y1, 'right':x1, 'bottom':y0})
                continue
            elif 'is_not_math' not in r['detection_list'] and not r['error']: # equation in standalone figure
                text = r['latex_styled'] if 'latex_styled' in r else r['latex_normal'] # possibly analyze for text vs. eqn
                conf = r['latex_confidence_rate']
                
                # may use bounding box returned in r['position'] to fine tune coordinates
                equations.append({'latex':text, 'conf':conf, 'left':x0, 'top':y0, 'right':x1, 'bottom':y1})
                continue
            else: # may also check is_blank etc.
                continue

            figures.append({'type':typ, 'left':x0, 'top':y0, 'right':x1, 'bottom':y1})
            
            
        return lines, images, paragraphs, equations, tables, figures
    
    

    def query(self, file_path, print=True, img=None):
        'Query server for single image'
        
        if img is not None:
            imgbin = cv2.imencode('.jpg', img)[1]
        else:
            imgbin = open(file_path, "rb").read()
        image_uri = "data:image/jpg;base64," + base64.b64encode(imgbin).decode()
        r = requests.post("https://api.mathpix.com/v3/latex",
                          data=json.dumps({'src': image_uri, 'formats': ['latex_normal', 'latex_styled']}),
                          headers=self.headers)
        if not print:
            return json.loads(r.text)
        return json.dumps(json.loads(r.text), indent=4, sort_keys=True)


    
## Testing
    
def process(img_path, rects):
    '''
    Receives image of note and rectangles (containing lines, figures etc.) in it, sends each rectangle to Mathpix server, and returns output to each rectangle.
    
    Inputs:
    img_path: path to image
    rects: list of rectangles, represented as tuple (x0,y0,x1,y1), x0<x1, y0<y1, possibly with info regarding e.g. whether it is a line or a figure
    
    Output: list containing a tuple (type, data, conf) for each rectangle
    type: what type of data the rectangle contains (text, math, chart, graph, diagram, table)
    data: in case of text, equation and table, what is written in the rectangle (plain text, latex etc.); otherwise None
    conf: confidence rate returned by API
    '''
    res = []
    img = cv2.imread(img_path)
    for i, rect in enumerate(rects):
        # crop image
        x0, y0, x1, y1 = rect # decide on this order
        cropped = img[y0:y1, x0:x1]
        
        # send request (may later do these in batch)
        r = query(img_path, False, cropped)
        
        # identify type
        if 'contains_graph' in r['detection_list']:
            typ = 'graph'
        elif 'contains_chart' in r['detection_list']:
            typ = 'chart'
        elif 'contains_diagram' in r['detection_list']:
            typ = 'diagram'
        elif 'contains_table' in r['detection_list']:
            typ = 'table'
        elif 'is_not_math' in r['detection_list']: # may not represent text; analyze latex for this
            typ = 'text'
        else: # may also check is_blank etc.
            typ = 'math'
        
        # if no error, fill data
        data = conf = None
        if not r['error']:
            data = r['latex_styled'] if 'latex_styled' in r else r['latex_normal'] # possibly analyze for text vs. eqn
            conf = r['latex_confidence_rate']
        
        res.append((typ, data, conf))
    return res

def query(file_path, print=True, img=None):
    if img is not None:
        imgbin = cv2.imencode('.jpg', img)[1]
    else:
        imgbin = open(file_path, "rb").read()
    image_uri = "data:image/jpg;base64," + base64.b64encode(imgbin).decode()
    r = requests.post("https://api.mathpix.com/v3/latex",
        data=json.dumps({'src': image_uri,
            'formats': ['latex_normal', 'latex_styled']}),
        headers=headers)
    if not print:
        return json.loads(r.text)
    return json.dumps(json.loads(r.text), indent=4, sort_keys=True)

