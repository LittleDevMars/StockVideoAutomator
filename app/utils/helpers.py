from typing import Optional, Union
import os
import sys
import re


def resource_path(*paths: str) -> str:
    """PyInstaller 빌드 환경에서도 올바른 리소스 경로를 반환한다."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        # 개발 환경: 프로젝트 루트 (helpers.py → utils → app → project root)
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *paths)


def format_file_size(size_bytes: Union[int, float, None]) -> str:
    if not size_bytes:
        return "알 수 없음"
    size_bytes = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "00:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_speed(bytes_per_sec: Optional[float]) -> str:
    if not bytes_per_sec:
        return ""
    return f"{format_file_size(bytes_per_sec)}/s"


def is_youtube_url(url: str) -> bool:
    patterns = [
        r"(https?://)?(www\.)?youtube\.com/watch\?v=",
        r"(https?://)?(www\.)?youtube\.com/playlist\?list=",
        r"(https?://)?(www\.)?youtube\.com/shorts/",
        r"(https?://)?youtu\.be/",
        r"(https?://)?(www\.)?youtube\.com/@[\w-]+",
        r"(https?://)?(www\.)?youtube\.com/channel/",
    ]
    return any(re.search(p, url) for p in patterns)


def is_playlist_url(url: str) -> bool:
    return "playlist?list=" in url or "&list=" in url
