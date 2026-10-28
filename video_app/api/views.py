from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import VideoSerializer
from video_app.models import Video
from pathlib import Path
from django.conf import settings
from django.http import FileResponse
import re


class VideoListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VideoSerializer
    queryset = Video.objects.all()



class HLSPlaylistView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        allowed_resolutions = ["480p", "720p", "1080p"]
        if resolution not in allowed_resolutions:
            return Response({"detail": "Resolution not found."}, status=status.HTTP_404_NOT_FOUND)
        playlist_path = Path(settings.MEDIA_ROOT) / "hls" / str(movie_id) / resolution / "index.m3u8"
        if not playlist_path.is_file():
            return Response({"detail": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(playlist_path.open("rb"), content_type="application/vnd.apple.mpegurl")

        
class HLSSegmentView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
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

        