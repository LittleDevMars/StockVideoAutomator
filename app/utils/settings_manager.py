"""Centralized settings manager using QSettings for persistence."""

import os
import sys
from PyQt6.QtCore import QSettings


class SettingsManager:
    """Read/write application settings backed by the Windows registry
    (or INI on other platforms)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._qs = QSettings("StockVideoAutomator", "SVA")
        return cls._instance

    # ── General ──────────────────────────────────────────

    @property
    def language(self) -> str:
        return self._qs.value("general/language", "한국어", type=str)

    @language.setter
    def language(self, v: str):
        self._qs.setValue("general/language", v)

    @property
    def run_in_background(self) -> bool:
        return self._qs.value("general/run_in_background", False, type=bool)

    @run_in_background.setter
    def run_in_background(self, v: bool):
        self._qs.setValue("general/run_in_background", v)

    @property
    def auto_start(self) -> bool:
        return self._qs.value("general/auto_start", False, type=bool)

    @auto_start.setter
    def auto_start(self, v: bool):
        self._qs.setValue("general/auto_start", v)

    @property
    def auto_update(self) -> bool:
        return self._qs.value("general/auto_update", False, type=bool)

    @auto_update.setter
    def auto_update(self, v: bool):
        self._qs.setValue("general/auto_update", v)

    @property
    def beta_enabled(self) -> bool:
        return self._qs.value("general/beta_enabled", False, type=bool)

    @beta_enabled.setter
    def beta_enabled(self, v: bool):
        self._qs.setValue("general/beta_enabled", v)

    # ── Advanced ─────────────────────────────────────────

    @property
    def concurrent_downloads(self) -> int:
        return self._qs.value("advanced/concurrent_downloads", 3, type=int)

    @concurrent_downloads.setter
    def concurrent_downloads(self, v: int):
        self._qs.setValue("advanced/concurrent_downloads", v)

    @property
    def download_threads(self) -> int:
        return self._qs.value("advanced/download_threads", 4, type=int)

    @download_threads.setter
    def download_threads(self, v: int):
        self._qs.setValue("advanced/download_threads", v)

    @property
    def default_save_path(self) -> str:
        default = os.path.join(os.path.expanduser("~"), "Videos")
        return self._qs.value("advanced/default_save_path", default, type=str)

    @default_save_path.setter
    def default_save_path(self, v: str):
        self._qs.setValue("advanced/default_save_path", v)

    @property
    def filename_numbering(self) -> bool:
        return self._qs.value("advanced/filename_numbering", False, type=bool)

    @filename_numbering.setter
    def filename_numbering(self, v: bool):
        self._qs.setValue("advanced/filename_numbering", v)

    # ── Connection ───────────────────────────────────────

    @property
    def proxy_type(self) -> str:
        return self._qs.value("connection/proxy_type", "사용 안 함", type=str)

    @proxy_type.setter
    def proxy_type(self, v: str):
        self._qs.setValue("connection/proxy_type", v)

    @property
    def proxy_host(self) -> str:
        return self._qs.value("connection/proxy_host", "", type=str)

    @proxy_host.setter
    def proxy_host(self, v: str):
        self._qs.setValue("connection/proxy_host", v)

    @property
    def proxy_port(self) -> str:
        return self._qs.value("connection/proxy_port", "", type=str)

    @proxy_port.setter
    def proxy_port(self, v: str):
        self._qs.setValue("connection/proxy_port", v)

    @property
    def speed_limit(self) -> int:
        """KB/s, 0 = unlimited."""
        return self._qs.value("connection/speed_limit", 0, type=int)

    @speed_limit.setter
    def speed_limit(self, v: int):
        self._qs.setValue("connection/speed_limit", v)

    # ── Notifications ────────────────────────────────────

    @property
    def notify_download_complete(self) -> bool:
        return self._qs.value("notification/download_complete", True, type=bool)

    @notify_download_complete.setter
    def notify_download_complete(self, v: bool):
        self._qs.setValue("notification/download_complete", v)

    @property
    def notify_download_error(self) -> bool:
        return self._qs.value("notification/download_error", True, type=bool)

    @notify_download_error.setter
    def notify_download_error(self, v: bool):
        self._qs.setValue("notification/download_error", v)

    @property
    def notify_sound(self) -> bool:
        return self._qs.value("notification/sound", False, type=bool)

    @notify_sound.setter
    def notify_sound(self, v: bool):
        self._qs.setValue("notification/sound", v)

    @property
    def notify_tray(self) -> bool:
        return self._qs.value("notification/tray", True, type=bool)

    @notify_tray.setter
    def notify_tray(self, v: bool):
        self._qs.setValue("notification/tray", v)

    # ── Authorization ────────────────────────────────────

    @property
    def cookie_browser(self) -> str:
        return self._qs.value("auth/cookie_browser", "사용 안 함", type=str)

    @cookie_browser.setter
    def cookie_browser(self, v: str):
        self._qs.setValue("auth/cookie_browser", v)

    # ── Toolbar state ─────────────────────────────────────

    @property
    def toolbar_download_type(self) -> str:
        return self._qs.value("toolbar/download_type", "video", type=str)

    @toolbar_download_type.setter
    def toolbar_download_type(self, v: str):
        self._qs.setValue("toolbar/download_type", v)

    @property
    def toolbar_format(self) -> str:
        return self._qs.value("toolbar/format", "mp4", type=str)

    @toolbar_format.setter
    def toolbar_format(self, v: str):
        self._qs.setValue("toolbar/format", v)

    @property
    def toolbar_format_label(self) -> str:
        return self._qs.value("toolbar/format_label", "MP4", type=str)

    @toolbar_format_label.setter
    def toolbar_format_label(self, v: str):
        self._qs.setValue("toolbar/format_label", v)

    @property
    def toolbar_quality(self) -> str:
        return self._qs.value("toolbar/quality", "best", type=str)

    @toolbar_quality.setter
    def toolbar_quality(self, v: str):
        self._qs.setValue("toolbar/quality", v)

    @property
    def toolbar_quality_label(self) -> str:
        return self._qs.value("toolbar/quality_label", "최고", type=str)

    @toolbar_quality_label.setter
    def toolbar_quality_label(self, v: str):
        self._qs.setValue("toolbar/quality_label", v)

    @property
    def toolbar_codec(self) -> str:
        return self._qs.value("toolbar/codec", "H264", type=str)

    @toolbar_codec.setter
    def toolbar_codec(self, v: str):
        self._qs.setValue("toolbar/codec", v)

    @property
    def toolbar_frame_rate(self) -> str:
        return self._qs.value("toolbar/frame_rate", "최고", type=str)

    @toolbar_frame_rate.setter
    def toolbar_frame_rate(self, v: str):
        self._qs.setValue("toolbar/frame_rate", v)

    @property
    def toolbar_subtitle_enabled(self) -> bool:
        return self._qs.value("toolbar/subtitle_enabled", False, type=bool)

    @toolbar_subtitle_enabled.setter
    def toolbar_subtitle_enabled(self, v: bool):
        self._qs.setValue("toolbar/subtitle_enabled", v)

    @property
    def toolbar_subtitle_lang(self) -> str:
        return self._qs.value("toolbar/subtitle_lang", "한국어", type=str)

    @toolbar_subtitle_lang.setter
    def toolbar_subtitle_lang(self, v: str):
        self._qs.setValue("toolbar/subtitle_lang", v)

    @property
    def toolbar_audio_track(self) -> str:
        return self._qs.value("toolbar/audio_track", "기본", type=str)

    @toolbar_audio_track.setter
    def toolbar_audio_track(self, v: str):
        self._qs.setValue("toolbar/audio_track", v)

    # ── Helpers ──────────────────────────────────────────

    def get_proxy_url(self) -> str:
        """Build proxy URL for yt-dlp. Returns empty string if disabled."""
        if self.proxy_type == "사용 안 함" or not self.proxy_host:
            return ""
        scheme = "socks5" if self.proxy_type == "SOCKS5" else "http"
        port = f":{self.proxy_port}" if self.proxy_port else ""
        return f"{scheme}://{self.proxy_host}{port}"

    def get_cookie_browser_name(self) -> str:
        """Return yt-dlp compatible browser name or empty string."""
        mapping = {
            "사용 안 함": "",
            "Chrome": "chrome",
            "Firefox": "firefox",
            "Edge": "edge",
            "Brave": "brave",
        }
        return mapping.get(self.cookie_browser, "")

    def get_auto_start_path(self) -> str:
        """Return the executable path for auto-start registration."""
        if getattr(sys, "frozen", False):
            return sys.executable
        return os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "main.py"
        ))

    def sync(self):
        self._qs.sync()
