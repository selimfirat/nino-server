import requests
from abbyy_sdk import *
import os
import time

class AbbyyRepository:
    
    def __init__(self):
        
        self.processor = AbbyyOnlineSdk()
                
        if "ABBYY_APPID" in os.environ:
            self.processor.ApplicationId = os.environ["ABBYY_APPID"]
        else:
            raise

        if "ABBYY_PWD" in os.environ:
            self.processor.Password = os.environ["ABBYY_PWD"]
        else:
            raise
            
        print(self.processor.ApplicationId, self.processor.Password)
    
    def process_image(self, source_image_path, target_file_path):
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

        if task.Status == "Completed":
            if task.DownloadUrl is not None:
                self.processor.download_result(task, target_file_path)
                print("Result was written to {}".format(target_file_path))
        else:
            print("Error processing task")

    
if __name__ == "__main__":

    # NinoNoteApp", "m2lyxzgZOaKmKWygyRGohxKD
    abby = AbbyyRepository()
    
    abby.process_image(source_image_path="temp_sample/MobPhoto_2.jpg", target_file_path="temp_sample/mob_photo2.xml")