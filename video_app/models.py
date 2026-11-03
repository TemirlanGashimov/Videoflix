"""Database models for videos and their associated media."""

from django.db import models


class Video(models.Model):
    """A video catalog entry and its optional source media file."""

    CATEGORY_CHOICES = [
        ("Action", "Action"),
        ("Comedy", "Comedy"),
        ("Drama", "Drama"),
        ("Documentary", "Documentary"),
        ("Horror", "Horror"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(
        upload_to="thumbnails/",
        blank=True,
        null=True,
    )
    category = models.CharField(
        max_length=255,
        choices=CATEGORY_CHOICES,
    )
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
