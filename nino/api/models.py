from django.db import models

class Note(models.Model):

    owner = models.ForeignKey('auth.User', related_name='notes', on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to="notes/original_images/", null=True, blank=True)
    
    def __str__(self):
        return "{}".format(self.name)

