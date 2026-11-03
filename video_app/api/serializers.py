"""Serializers for video catalog API responses."""

from rest_framework import serializers
from video_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    """Serialize the public catalog fields of a video."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        """Select the model and fields exposed by the video API."""

        model = Video
        fields = ["id", "created_at", "title", "description", "thumbnail_url", "category"]

    def get_thumbnail_url(self, obj):
        """Return the URL of the generated thumbnail."""
        if not obj.thumbnail:
            return None
        return self.context["request"].build_absolute_uri(obj.thumbnail.url)