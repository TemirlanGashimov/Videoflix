"""Application configuration for the video app."""

from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """Configure the video app and load its signal handlers."""

    name = 'video_app'

    def ready(self):
        """Import signal handlers after the Django app registry is ready."""
        from . import signals
