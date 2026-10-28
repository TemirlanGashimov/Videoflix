"""Authenticated endpoints for HLS playlists and media segments."""

from pathlib import Path
from django.conf import settings
from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import re


class HLSPlaylistView(generics.GenericAPIView):
    """Serve an existing HLS playlist at an allowed resolution."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """Return the requested playlist or a not-found response."""
        allowed_resolutions = ["480p", "720p", "1080p"]
        if resolution not in allowed_resolutions:
            return Response({"detail": "Resolution not found."}, status=status.HTTP_404_NOT_FOUND)
        playlist_path = Path(settings.MEDIA_ROOT) / "hls" / str(movie_id) / resolution / "index.m3u8"
        if not playlist_path.is_file():
            return Response({"detail": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(playlist_path.open("rb"), content_type="application/vnd.apple.mpegurl")


class HLSSegmentView(generics.GenericAPIView):
    """Serve an existing HLS transport-stream segment."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """Return a validated segment path or a not-found response."""
        allowed_resolutions = ["480p", "720p", "1080p"]
        if resolution not in allowed_resolutions:
            return Response({"detail": "Resolution not found."}, status=status.HTTP_404_NOT_FOUND)
        if not segment.endswith(".ts"):
            return Response({"detail": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)
        if not re.fullmatch(r"segment_\d{3}\.ts", segment):
            return Response({"detail": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)
        segment_path = Path(settings.MEDIA_ROOT)/"hls"/str(movie_id)/resolution/segment
        if not segment_path.is_file():
            return Response({"detail": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)
        
        return FileResponse(segment_path.open("rb"), content_type="video/MP2T")