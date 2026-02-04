from dataclasses import dataclass, field


@dataclass
class VideoInfo:
    url: str = ""
    video_id: str = ""
    title: str = ""
    channel: str = ""
    duration: int = 0  # seconds
    thumbnail_url: str = ""
    formats: list = field(default_factory=list)
    subtitles: dict = field(default_factory=dict)
    auto_captions: dict = field(default_factory=dict)
    is_playlist: bool = False
    playlist_title: str = ""
    playlist_index: int = 0
    playlist_count: int = 0

    # Set after format selection
    selected_format: str = ""
    selected_quality: str = ""
    filesize_approx: int = 0
    resolution: str = ""
    fps: int = 0
    ext: str = ""

    # Internal
    added_index: int = 0  # 추가 순서 (정렬용)

    # Download state
    status: str = "pending"  # pending, downloading, completed, error, cancelled
    progress: float = 0.0
    speed: float = 0.0
    eta: int = 0
    downloaded_path: str = ""
    error_message: str = ""
    download_type: str = "video"  # video or audio
