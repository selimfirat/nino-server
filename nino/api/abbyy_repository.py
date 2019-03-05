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
            time.sleep(3)
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
        blocksxml = xmldoc.getElementsByTagName("page")[0].getElementsByTagName('block')

        lines = []
        for block in blocksxml:
            textNodes = block.getElementsByTagName("text")

            if len(textNodes) == 0:
                continue

            pars = textNodes[0].getElementsByTagName("par")

            for par in pars:
                linesObj = par.getElementsByTagName("line")
                for lineObj in linesObj:
                    l, b, r, t = int(lineObj.getAttribute("l")), int(lineObj.getAttribute("t")), int(lineObj.getAttribute("r")), int(lineObj.getAttribute("b"))
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

                    lines.append(line_dict)

        return lines
        
if __name__ == "__main__":

    # NinoNoteApp", "m2lyxzgZOaKmKWygyRGohxKD
    abby = AbbyyRepository("ocrappaccount", "xkwNVKxJWduwFXUVHrBEZZmT")
    
    res = abby.process_image(source_image_path="temp_sample/MobPhoto_2.jpg")
    
    print(res)