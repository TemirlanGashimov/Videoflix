"""Admin configuration for managing video catalog entries."""

from django.contrib import admin
from .models import Video

class VideoAdmin(admin.ModelAdmin):
    """Admin options for video records."""

    exclude = ("thumbnail",)


admin.site.register(Video, VideoAdmin)