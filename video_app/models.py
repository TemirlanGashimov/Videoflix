from django.db import models


class Video(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail_url = models.URLField()
    category = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
