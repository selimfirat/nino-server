# Exporting to LaTeX with Textpos

# Given dictionary jres with lines, images, equations etc., call LatexExporter().export(jres, out) to write tex file to out

import io
import os
import os.path

class LatexExporter:
    def __init__(self):
        
        # later modify this to change size of document
        self.header = '''
\\documentclass{article}

\\usepackage[absolute]{textpos}
\\usepackage{amsmath}
\\usepackage[utf8]{inputenc}

\\setlength{\\TPHorizModule}{30mm}
\\setlength{\\TPVertModule}{\TPHorizModule}
\\textblockorigin{0mm}{0mm}

\\setlength{\\parindent}{0pt}
\\pagestyle{empty}

\\begin{document}
        '''
        
        self.footer = '\\end{document}'
        
        self.replace = [('\\', '\\(\\backslash\\)'), ('<', '\\textless\\'), ('>', '\\textgreater\\'),
                        ('%', '\\%'), ('$', '\\$'), ('{', '\\{'), ('}', '\\}'), ('_', '\\_'), 
                        ('#', '\\#'), ('&', '\\&'), ('¶', '\\P\\'), ('§', '\\S\\'),
                        ('†', '\\dag\\'), ('‡', '\\ddag\\'), ('|', '\\textbar\\'), 
                        ('—', '\\textemdash'), ('–', '\\textendash\\'), 
                        ('¡', '\\textexclamdown\\'), ('¿', '\\textquestiondown\\'),
                        ('™', '\\texttrademark\\'), ('®', '\\textregistered\\'), 
                        ('ⓐ', '\\textcircled{a}'), ('©', '\\copyright\\')
                       ]
    
    def export(self, jres, out=None):
        '''Given json of note, generate LaTeX file with absolute positioning of boxes
        
        jres: dictionary containing lines, images, equations etc. keys
        out: output file path'''
        
        ppi = 300 # assumed for now, later calculate from image by fitting image into A4 size
        
        with (open(out, 'w') if out else io.StringIO()) as f:
            f.write(self.header)
            
            for line in jres['lines']:
                self.writeblock(f, line, ppi, self.guard(line['text']))
            
            for eqn in jres['equations']:
                self.writeblock(f, eqn, ppi)
            
            f.write(self.footer)
        
            if not out:
                return f.getvalue()
                
    def guard(self, text): # TODO remove unicode characters
        'Guard special characters in string'
        for c, s in self.replace:
            text = text.replace(c, s)
        return text
                
    def writeblock(self, f, line, ppi, text=None):
        if text is None:
            text = line['text']
        
        x0, y0, x1, y1 = line['left'], line['bottom'], line['right'], line['top']
                
        f.write('\n\\begin{textblock}{%.2f}(%.2f,%.2f)\n' % ((x1-x0)/ppi, x0/ppi, y0/ppi))
        f.write(text)
        f.write('\n\\end{textblock}\n')
            
class PDFExporter:
    def __init__(self):
        self.latexp = LatexExporter()

    def export(self, jres, out):
        if out[-4:] == '.pdf':
            out = out[:-4]
        
        self.latexp.export(jres, out + '.tex')
        
        dirname = os.path.dirname(out)
        os.system('rm -f %s.pdf' % out)
        os.system('latexmk -pdf -f -quiet -outdir=%s %s' % (dirname, out))
        os.system('latexmk -pdf -c -outdir=%s %s' % (dirname, out))
        
        # TODO check if pdf created normally
        
        return out + '.pdf'