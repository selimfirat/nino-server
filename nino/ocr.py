from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import xml.etree.ElementTree as ET
import pytesseract
import json
import re

class BBox:
    def __init__(self, x0, y0, x1, y1, c=100, text=None, children=None):
        self.x0 = int(x0)
        self.y0 = int(y0)
        self.x1 = int(x1)
        self.y1 = int(y1)
        self.c  = int(c)
        self.text = text or ''
        self.children = children or []
    
    def area(self):
        return (self.x1 - self.x0)*(self.y1-self.y0)
    
    def __add__(self, other):
        # smallest box containing both boxes
        x0 = min([self.x0, other.x0])
        y0 = min([self.y0, other.y0])
        x1 = max([self.x1, other.x1])
        y1 = max([self.y1, other.y1])
        # TODO detect whether rects are added vertically or horizontally
        left, right = (self, other) if x0 == self.x0 else (other, self)
        return BBox(x0, y0, x1, y1, min([self.c, other.c]), left.text + ' ' + right.text, [left, right])
    
    def __repr__(self):
        return 'BBox(%d, %d, %d, %d, %d, \'%s\', %s)' % (self.x0, self.y0, self.x1, self.y1, self.c, self.text, self.children)

class BBoxEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, list):
            return [self.default(a) for a in obj]
        if isinstance(obj, BBox):
            return {'text': obj.text, 'coords': [obj.x0, obj.y0, obj.x1, obj.y1], 'conf': obj.c,
                    'children': []} # self.default(obj.children)}
        return json.JSONEncoder.default(self, obj)

def bboxes(img):
    'Receive PIL Image, return list of bounding boxes along with modified image with boxes added.'
    # img = Image.open(img)
    hocr = pytesseract.image_to_pdf_or_hocr(img, extension='hocr')
    root = ET.fromstring(hocr)
    ns = list(ET._namespace_map.keys())[list(ET._namespace_map.values()).index('html')]
    img1 = img.copy()
    dr = ImageDraw.Draw(img1)
    rects = []
    for box in root.iter('{%s}span' % ns):
        if box.attrib['class'] == 'ocrx_word':
            [x0,y0,x1,y1,c] = re.findall('\d+', box.attrib['title'])
            dr.rectangle(((int(x0), int(y0)), (int(x1), int(y1))), outline=(255,0,0))
            while box.text is None:
                box = box[0]
            if box.text.isspace():
                continue
            rects.append(BBox(x0,y0,x1,y1,c,box.text))
            dr.text(((int(x0), int(y0)-10)), box.text.encode('ascii', 'replace'), fill=(0,0,0))
            dr.text(((int(x1)-5, int(y0)-10)), c, fill=(0,0,0))
            # print(box.text, x0, y0, x1, y1, c)
    del dr
    return img1, rects

def combine(img, rects, k):
    'Combine neighboring bounding boxes until k boxes left, return new list of boxes.'
    img1 = img.copy() # debugging
    dr = ImageDraw.Draw(img1)
    
    # simple procedure to combine closest pair of boxes similar to upgma or hierarchical clustering
    # cost to combine boxes: (area of new rectangle) - (areas of old rectangles)
    rects = list(rects)
    while len(rects) > k:
        min_i = min_j = 0
        min_sc = img.size[0] * img.size[1]
        for i, r1 in enumerate(rects):
            for j, r2 in enumerate(rects):
                if i <= j:
                    continue
                r = r1 + r2
                sc = r.area() - r1.area() - r2.area() # + r.c - r1.c - r2.c
                # sc /= r.area()
                if min_sc > sc:
                    min_sc = sc
                    min_i, min_j = i, j
        # print(min_sc, rects[min_i], rects[min_j], rects[min_i] + rects[min_j])
        dr.rectangle(((rects[min_i].x0, rects[min_i].y0), (rects[min_i].x1, rects[min_i].y1)), outline=(255,0,0))
        dr.rectangle(((rects[min_j].x0, rects[min_j].y0), (rects[min_j].x1, rects[min_j].y1)), outline=(255,0,0))
        rects[min_i] = rects[min_i] + rects[min_j]
        dr.rectangle(((rects[min_i].x0, rects[min_i].y0), (rects[min_i].x1, rects[min_i].y1)), outline=(0,255,0))
        rects.pop(min_j)
    del dr
    return img1, rects

def disp_rects(img, rects):
    img1 = img.copy()
    dr = ImageDraw.Draw(img1)
    for rect in rects:
        dr.rectangle(((rect.x0, rect.y0), (rect.x1, rect.y1)), outline=(255,0,0))
        dr.text(((rect.x0, rect.y0-10)), rect.text.encode('ascii', 'replace'), fill=(0,0,0))
        dr.text(((rect.x1-5, rect.y0-10)), str(rect.c), fill=(0,0,0))
    del dr
    return img1

if __name__ == '__main__':
    import sys
    if len(sys.argv) <= 2 or len(sys.argv) > 4:
        print('Format: ocr.py <input image filename> <no of boxes (0: do not combine)> [<output image filename>]')
        sys.exit(1)
    fin = sys.argv[1]
    k = int(sys.argv[2])
    fout = sys.argv[3] if len(sys.argv) == 4 else None
    
    img = Image.open(fin)
    _, rects = bboxes(img)
    
    if k > 0:
        _, rects = combine(img, rects, k)
    
    # print(rects)
    print(json.dumps(BBoxEncoder().default(rects), indent=2))
    if fout is not None:
        img1 = disp_rects(img, rects)
        img1.save(fout, 'PNG')
    sys.exit(0)
    