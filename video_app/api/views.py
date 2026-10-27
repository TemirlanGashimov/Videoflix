from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import VideoSerializer
from video_app.models import Video


class VideoListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VideoSerializer
    queryset = Video.objects.all()