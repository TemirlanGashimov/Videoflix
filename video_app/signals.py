"""Signals that enqueue background work when video records are created."""

from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save
import django_rq
from .tasks import convert_video_to_hls
from django.db import transaction

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """Queue HLS conversion after a newly uploaded video is committed."""
    if created and instance.video_file:
        queue = django_rq.get_queue(name="default")
        transaction.on_commit(lambda: queue.enqueue(convert_video_to_hls, instance.id))
