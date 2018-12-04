from nino.utils.rect import *
import nino.bbox.bbox as bb

def parse(layout, **kwargs):
    'Parse layout dictionary obtained from LayoutAnalysis.'
    n = bb.Note(**kwargs)
    visit_children(layout, n)
    return n

def visit_children(layout, bbox):
    if isinstance(layout, dict):
        for key in layout:
            visit(layout[key], bbox, key)
            
def visit(layout, bbox, key=None):
    if key == 'TextRegion':
        if isinstance(layout, dict):
            layout = [layout]
        for d in layout:
            bbox1 = bb.TextBBox(Rect(0,0,0,0))
            visit_children(d, bbox1)
            bbox.add_child(bbox1)
    elif key == 'TextLine':
        if isinstance(layout, dict):
            layout = [layout]
        for d in layout:
            bbox1 = bb.LineBBox(Rect(0,0,0,0))
            visit_children(d, bbox1)
            bbox.add_child(bbox1)
    elif key == 'Coords':
        pts = layout['@points'].split(' ')
        pts = [pt.split(',') for pt in pts]
        x0 = min(int(float(pt[0])) for pt in pts)
        y0 = min(int(float(pt[1])) for pt in pts)
        x1 = max(int(float(pt[0])) for pt in pts)
        y1 = max(int(float(pt[1])) for pt in pts)
        # x0, y0 = int(float(pt[0][0])), int(float(pt[0][1]))
        # x1, y1 = int(float(pt[2][0])), int(float(pt[2][1]))
        bbox.rect = Rect(x0,y0,x1,y1)
    elif key == 'Page':
        h = int(layout['@imageHeight'])
        w = int(layout['@imageWidth'])
        bbox.rect = Rect(0,0,w,h)
        visit_children(layout, bbox)
    else:
        visit_children(layout, bbox)