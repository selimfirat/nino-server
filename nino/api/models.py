from django.db import models

class TimestampedModel(models.Model):
    # A timestamp representing when this object was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # A timestamp reprensenting when this object was last updated.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

        # By default, any model that inherits from `TimestampedModel` should
        # be ordered in reverse-chronological order. We can override this on a
        # per-model basis as needed, but reverse-chronological is a good
        # default ordering for most models.
        ordering = ['-created_at', '-updated_at']

class Note(TimestampedModel):

    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to="notes/original_images/", null=True, blank=True)
    
    
    def __str__(self):
        return "{}".format(self.name)