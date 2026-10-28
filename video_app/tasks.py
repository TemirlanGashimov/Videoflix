from .models import Video
from django.conf import settings
from pathlib import Path
from subprocess import run


def convert_video_to_hls(video_id):
    video = Video.objects.get(id=video_id)
    if not video.video_file:
        raise ValueError("No video file available.")
    input_path = video.video_file.path
    output_dir = Path(settings.MEDIA_ROOT)/"hls" / str(video_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    resolutions = ["480p", "720p", "1080p"]
    resolution_heights = {"480p": 480, "720p": 720, "1080p": 1080}
    for resolution in resolutions:
        height = resolution_heights[resolution]
        scale_filter = f"scale=-2:{height}"
        resolution_dir = output_dir / resolution
        resolution_dir.mkdir(parents=True, exist_ok=True)
        playlist_path = resolution_dir / "index.m3u8"
        segment_path = str(resolution_dir / "segment_%03d.ts")
        command = ["ffmpeg", "-nostdin", "-y", "-i", input_path, "-vf", scale_filter, "-c:v", "libx264", "-threads", "1", "-c:a", 
                   "aac", "-f","hls", "-hls_time", "6", "-hls_playlist_type", "vod", "-hls_segment_filename", 
                   segment_path, str(playlist_path)]
        run(command, check=True)
