import requests
from .abbyy_sdk import *
import os
import time
from xml.dom import minidom
import uuid

class AbbyyRepository:
    
    def __init__(self, appid=None, pwd=None):
        
        self.processor = AbbyyOnlineSdk()
        
        if appid is not None:
            self.processor.ApplicationId = appid
            self.processor.Password = pwd
        else:
            if "ABBYY_APPID" in os.environ:
                self.processor.ApplicationId = os.environ["ABBYY_APPID"]
            else:
                raise

            if "ABBYY_PWD" in os.environ:
                self.processor.Password = os.environ["ABBYY_PWD"]
            else:
                raise
            
        # print(self.processor.ApplicationId, self.processor.Password)
    
    def process_image(self, source_image_path):
        print("Uploading..")
        settings = ProcessingSettings()
        settings.Language = "English"
        settings.OutputFormat = "xml"
        
        task = self.processor.process_image(source_image_path, settings)
        
        if task is None:
            print("Error")
            return
        if task.Status == "NotEnoughCredits":
            print("Not enough credits to process the document. Please add more pages to your application's account.")
            return

        print("Id = {}".format(task.Id))
        print("Status = {}".format(task.Status))

        # Wait for the task to be completed
        print("Waiting..")

        while task.is_active():
            time.sleep(0.5)
            print(".")
            task = self.processor.get_task_status(task)

        print("Status = {}".format(task.Status))

        target_file_path = str(uuid.uuid4()) + ".xml"
        if task.Status == "Completed":
            if task.DownloadUrl is not None:
                self.processor.download_result(task, target_file_path)
                print("Result was written to {}".format(target_file_path))
        else:
            print("Error processing task")
        
        jres = self.xml_to_json(target_file_path)

        os.remove(target_file_path)
        
        return jres

    def xml_to_json(self, f_xml):
        xmldoc = minidom.parse(f_xml)
        print(xmldoc)
        pagexml = xmldoc.getElementsByTagName("page")[0]
        page = {
            "width": pagexml.getAttribute("width"),
            "height": pagexml.getAttribute("height")
        }
        blocksxml = pagexml.getElementsByTagName('block')

        lines = []
        images = []
        paragraphs = []
        for block in blocksxml:
            block_type = block.getAttribute("blockType")
            
            if block_type == "Text":
                textNodes = block.getElementsByTagName("text")

                if len(textNodes) == 0:
                    continue

                pars = textNodes[0].getElementsByTagName("par")

                for par in pars:
                    linesObj = par.getElementsByTagName("line")
                    par_lines = []
                    for lineObj in linesObj:
                        l, b, r, t = int(lineObj.getAttribute("l")), int(lineObj.getAttribute("b")), int(lineObj.getAttribute("r")), int(lineObj.getAttribute("t"))
                        charsObj = lineObj.getElementsByTagName("formatting")[0].getElementsByTagName("charParams")
                        lineText = ""
                        for charObj in charsObj:

                            lineText += charObj.firstChild.nodeValue

                        line_dict = {
                            "text": lineText,
                            "left": l,
                            "top": t,
                            "right": r,
                            "bottom": b
                        }

                        par_lines.append(line_dict)
                    lines.extend(par_lines)
                    
                    par_text = ""
                    par_left = 9999999
                    par_right = -9999999
                    par_top = 9999999
                    par_bottom = -9999999
                    for par_line in par_lines:
                        par_text += par_line["text"] + " \n "
                        par_left = min(par_line["left"], par_left)
                        par_right = max(par_line["right"], par_right)
                        par_top = min(par_line["top"], par_top)
                        par_bottom = max(par_line["bottom"], par_bottom)
                    
                    paragraph_dict = {
                        "text": par_text,
                        "left": par_left,
                        "top": par_top,
                        "right": par_right,
                        "bottom": par_bottom
                    }
                    
                    if par_text != "":
                        paragraphs.append(paragraph_dict)
                    
            elif block_type == "Picture":
                l, b, r, t = int(block.getAttribute("l")), int(block.getAttribute("b")), int(block.getAttribute("r")), int(block.getAttribute("t"))
                
                image_dict = {
                            "left": l,
                            "top": t,
                            "right": r,
                            "bottom": b
                        }
                
                images.append(image_dict)


        
        return page, lines, images, paragraphs
        
if __name__ == "__main__":

    # NinoNoteApp", "m2lyxzgZOaKmKWygyRGohxKD
    abby = AbbyyRepository("testsdaads", "rcFeQe5N3kRGiZx4ZbLSIuJu")
    
    res = abby.process_image(source_image_path="temp_sample/MobPhoto_2.jpg")
    
    print(res)