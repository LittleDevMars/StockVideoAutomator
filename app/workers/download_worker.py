import os
import shutil
import sys
import time
from PyQt6.QtCore import QThread, pyqtSignal

from app.models.video_info import VideoInfo
from app.utils.settings_manager import SettingsManager


class DownloadWorker(QThread):
    """Worker thread to download a video/audio using yt-dlp."""

    progress = pyqtSignal(str, dict)  # video_id, progress_data
    finished = pyqtSignal(str, str)   # video_id, file_path
    error = pyqtSignal(str, str)      # video_id, error_message

    # 자막 언어 → yt-dlp 언어코드
    LANG_MAP = {
        "한국어": "ko", "English": "en", "日本語": "ja", "中文": "zh",
    }
    # 코덱 → yt-dlp vcodec 필터 접두어
    CODEC_MAP = {
        "H264": "avc1", "H265": "hev", "VP9": "vp9", "AV1": "av01",
    }
    # 프레임 속도 → fps 값
    FPS_MAP = {
        "최고": 0, "60fps": 60, "30fps": 30, "24fps": 24,
    }

    def __init__(self, video_info: VideoInfo, save_dir: str,
                 download_type: str = "video", quality: str = "best",
                 fmt: str = "mp4", subtitle: bool = False,
                 subtitle_lang: str = "한국어",
                 audio_track: str = "기본",
                 frame_rate: str = "최고",
                 codec: str = "H264",
                 parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self.save_dir = save_dir
        self.download_type = download_type
        self.quality = quality
        self.fmt = fmt
        self.subtitle = subtitle
        self.subtitle_lang = subtitle_lang
        self.audio_track = audio_track
        self.frame_rate = frame_rate
        self.codec = codec
        self._cancelled = False
        self._downloaded_filepath = ""
        self._last_emit_time = 0.0
        self._settings = SettingsManager()

    def cancel(self):
        self._cancelled = True

    def run(self):
        import yt_dlp
        self._yt_dlp = yt_dlp

        vid = self.video_info.video_id
        try:
            ydl_opts = self._build_options()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.video_info.url, download=True)
                if info:
                    # Get the actual output filename from yt-dlp
                    self._downloaded_filepath = ydl.prepare_filename(info)
                    # For audio postprocessing, extension changes
                    if self.download_type == "audio":
                        base = os.path.splitext(self._downloaded_filepath)[0]
                        codec = self.fmt if self.fmt in ("mp3", "m4a", "wav", "flac") else "mp3"
                        self._downloaded_filepath = base + "." + codec

            if self._cancelled:
                self.error.emit(vid, "다운로드가 취소되었습니다.")
                return

            self.finished.emit(vid, self._downloaded_filepath)

        except Exception as e:
            if self._cancelled:
                self.error.emit(vid, "다운로드가 취소되었습니다.")
            else:
                self.error.emit(vid, str(e))

    def _build_options(self) -> dict:
        output_template = os.path.join(self.save_dir, "%(title)s.%(ext)s")

        opts = {
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
        }

        # deno 경로 자동 추가 (yt-dlp JS 런타임)
        deno_dir = os.path.join(os.path.expanduser("~"), ".deno", "bin")
        if os.path.isdir(deno_dir) and deno_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = deno_dir + os.pathsep + os.environ.get("PATH", "")

        # ffmpeg 경로 자동 탐색
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            # 알려진 경로에서 찾기
            candidates = [
                os.path.join(os.path.dirname(sys.executable), "Scripts", "ffmpeg.exe"),
                r"E:\Python\Scripts\ffmpeg.exe",
                os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "ffmpeg", "ffmpeg.exe"),
            ]
            for candidate in candidates:
                if os.path.isfile(candidate):
                    ffmpeg_path = candidate
                    break
        if ffmpeg_path:
            opts["ffmpeg_location"] = os.path.dirname(ffmpeg_path)

        if self.download_type == "audio":
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.fmt if self.fmt in ("mp3", "m4a", "wav", "flac") else "mp3",
                "preferredquality": "192",
            }]
        else:
            fmt_str = self._get_format_string()
            opts["format"] = fmt_str
            if self.fmt in ("mp4", "mkv", "webm"):
                opts["merge_output_format"] = self.fmt

        if self.subtitle:
            opts["writesubtitles"] = True
            opts["writeautomaticsub"] = True
            lang_code = self.LANG_MAP.get(self.subtitle_lang, "ko")
            opts["subtitleslangs"] = [lang_code]

        # 오디오 트랙: "모든 트랙"이면 모든 오디오 스트림 포함
        if self.audio_track == "모든 트랙" and self.download_type == "video":
            opts["format_sort"] = ["hasaud"]
            opts["postprocessors"] = opts.get("postprocessors", []) + [{
                "key": "FFmpegMerger",
            }]

        # ── Settings from preferences ──
        s = self._settings

        # Proxy
        proxy_url = s.get_proxy_url()
        if proxy_url:
            opts["proxy"] = proxy_url

        # Speed limit (KB/s → B/s)
        if s.speed_limit > 0:
            opts["ratelimit"] = s.speed_limit * 1024

        # Download threads (concurrent fragment downloads)
        threads = s.download_threads
        if threads > 1:
            opts["concurrent_fragment_downloads"] = threads

        # Browser cookies
        browser_name = s.get_cookie_browser_name()
        if browser_name:
            opts["cookiesfrombrowser"] = (browser_name,)

        return opts

    def _get_format_string(self) -> str:
        # 화질 필터
        if self.quality == "best":
            height_filter = ""
        else:
            h = self.quality.replace("p", "")
            height_filter = f"[height<={h}]"

        # 코덱 필터
        codec_prefix = self.CODEC_MAP.get(self.codec, "")
        codec_filter = f"[vcodec^={codec_prefix}]" if codec_prefix else ""

        # 프레임 속도 필터
        fps_val = self.FPS_MAP.get(self.frame_rate, 0)
        fps_filter = f"[fps<={fps_val}]" if fps_val > 0 else ""

        vf = f"{height_filter}{codec_filter}{fps_filter}"
        return f"bestvideo{vf}+bestaudio/bestvideo{height_filter}+bestaudio/best"

    # 시그널 스로틀링 간격 (초)
    THROTTLE_INTERVAL = 0.3

    def _progress_hook(self, d: dict):
        if self._cancelled:
            raise self._yt_dlp.utils.DownloadError("Cancelled")

        vid = self.video_info.video_id
        if d["status"] == "downloading":
            now = time.monotonic()
            if now - self._last_emit_time < self.THROTTLE_INTERVAL:
                return
            self._last_emit_time = now

            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed") or 0
            eta = d.get("eta") or 0
            pct = (downloaded / total * 100) if total > 0 else 0

            self.progress.emit(vid, {
                "progress": pct,
                "downloaded": downloaded,
                "total": total,
                "speed": speed,
                "eta": eta,
                "status": "downloading",
            })
        elif d["status"] == "finished":
            self.progress.emit(vid, {
                "progress": 100.0,
                "status": "processing",
            })

