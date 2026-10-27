from django.urls import path
from .views import VideoListView, HLSPlaylistView

urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', HLSPlaylistView.as_view(), name='hls-playlist'),
]
