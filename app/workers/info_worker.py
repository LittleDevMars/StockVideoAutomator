from PyQt6.QtCore import QThread, pyqtSignal

from app.models.video_info import VideoInfo
from app.utils.helpers import is_playlist_url


class InfoWorker(QThread):
    """Worker thread to fetch video/playlist info using yt-dlp."""

    info_ready = pyqtSignal(VideoInfo)
    playlist_ready = pyqtSignal(list)  # list[VideoInfo]
    error = pyqtSignal(str)
    status_message = pyqtSignal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        import yt_dlp
        self._yt_dlp = yt_dlp

        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"],
                    }
                },
            }

            if is_playlist_url(self.url):
                self._fetch_playlist(ydl_opts)
            else:
                self._fetch_single(ydl_opts)

        except Exception as e:
            self.error.emit(f"정보를 가져오는 중 오류 발생: {str(e)}")

    def _fetch_single(self, ydl_opts: dict):
        self.status_message.emit("영상 정보를 가져오는 중...")
        with self._yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
            if info is None:
                self.error.emit("영상 정보를 가져올 수 없습니다.")
                return
            video_info = self._parse_info(info)
            self.info_ready.emit(video_info)

    def _fetch_playlist(self, ydl_opts: dict):
        self.status_message.emit("재생목록 정보를 가져오는 중...")
        with self._yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
            if info is None:
                self.error.emit("재생목록 정보를 가져올 수 없습니다.")
                return

            entries = info.get("entries", [])
            if not entries:
                self.error.emit("재생목록에 영상이 없습니다.")
                return

            playlist_title = info.get("title", "재생목록")
            videos = []
            total = len(entries)

            for i, entry in enumerate(entries):
                if entry is None:
                    continue
                self.status_message.emit(
                    f"재생목록 정보 가져오는 중... ({i + 1}/{total})"
                )
                vi = self._parse_info(entry)
                vi.is_playlist = True
                vi.playlist_title = playlist_title
                vi.playlist_index = i + 1
                vi.playlist_count = total
                videos.append(vi)

            self.playlist_ready.emit(videos)

    def _parse_info(self, info: dict) -> VideoInfo:
        formats = info.get("formats", [])
        best_video = None
        best_filesize = 0

        for f in formats:
            if f.get("vcodec", "none") != "none":
                fs = f.get("filesize") or f.get("filesize_approx") or 0
                if fs > best_filesize:
                    best_filesize = fs
                    best_video = f

        resolution = ""
        fps = 0
        if best_video:
            w = best_video.get("width", 0)
            h = best_video.get("height", 0)
            if h:
                resolution = f"{h}p"
            if w and h:
                resolution = f"{w}x{h}"
            fps = best_video.get("fps", 0) or 0

        return VideoInfo(
            url=info.get("webpage_url") or info.get("url", ""),
            video_id=info.get("id", ""),
            title=info.get("title", "제목 없음"),
            channel=info.get("uploader") or info.get("channel", "알 수 없음"),
            duration=info.get("duration") or 0,
            thumbnail_url=info.get("thumbnail", ""),
            formats=formats,
            subtitles=info.get("subtitles") or {},
            auto_captions=info.get("automatic_captions") or {},
            filesize_approx=best_filesize,
            resolution=resolution,
            fps=int(fps),
            ext=info.get("ext", "mp4"),
        )
