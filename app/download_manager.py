"""Manages download workers, queue, and progress tracking.

Extracted from MainWindow to separate download orchestration logic from UI.
"""

from collections import deque
from typing import Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from app.models.video_info import VideoInfo
from app.utils.settings_manager import SettingsManager


class DownloadManager(QObject):
    """Orchestrates download workers and the download queue."""

    # Signals for the UI to connect to
    download_progress = pyqtSignal(str, dict)     # video_id, progress_data
    download_finished = pyqtSignal(str, str)       # video_id, file_path
    download_error = pyqtSignal(str, str)          # video_id, error_message
    status_message = pyqtSignal(str)               # message for status bar

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._workers: Dict[str, "DownloadWorker"] = {}
        self._download_queue: deque = deque()

    # ── Public API ───────────────────────────────────────

    @property
    def active_count(self) -> int:
        return len(self._workers)

    @property
    def queued_count(self) -> int:
        return len(self._download_queue)

    def start_download(self, video_info: VideoInfo, save_dir: str,
                       download_type: str, quality: str, fmt: str,
                       subtitle: bool, subtitle_lang: str,
                       audio_track: str, frame_rate: str, codec: str):
        """Queue or start a download respecting concurrent limit."""
        max_concurrent = self._settings.concurrent_downloads
        if len(self._workers) >= max_concurrent:
            self._download_queue.append(
                _DownloadParams(video_info, save_dir, download_type, quality,
                                fmt, subtitle, subtitle_lang, audio_track,
                                frame_rate, codec)
            )
            return

        self._launch_worker(video_info, save_dir, download_type, quality,
                            fmt, subtitle, subtitle_lang, audio_track,
                            frame_rate, codec)

    def cancel_download(self, video_id: str):
        worker = self._workers.get(video_id)
        if worker:
            worker.cancel()

    def pause_all(self) -> list[str]:
        """Cancel all active workers and drain the queue.

        Returns a list of video_ids that were paused (active + queued).
        """
        paused_ids = []

        for vid, worker in list(self._workers.items()):
            worker.cancel()
            paused_ids.append(vid)
        self._workers.clear()

        for params in self._download_queue:
            paused_ids.append(params.video_info.video_id)
        self._download_queue.clear()

        return paused_ids

    def resume_downloads(self, items: list[tuple[VideoInfo, dict]]):
        """Re-queue a list of (VideoInfo, toolbar_params) for download.

        ``toolbar_params`` is a dict with keys: save_dir, download_type,
        quality, fmt, subtitle, subtitle_lang, audio_track, frame_rate, codec.
        """
        for vi, params in items:
            self.start_download(vi, **params)

    def cancel_all(self):
        """Cancel every active worker and clear the queue (for shutdown)."""
        for worker in list(self._workers.values()):
            worker.cancel()
            worker.wait(2000)
        self._workers.clear()
        self._download_queue.clear()

    # ── Internal ─────────────────────────────────────────

    def _launch_worker(self, video_info, save_dir, download_type, quality,
                       fmt, subtitle, subtitle_lang, audio_track,
                       frame_rate, codec):
        from app.workers.download_worker import DownloadWorker
        worker = DownloadWorker(
            video_info=video_info,
            save_dir=save_dir,
            download_type=download_type,
            quality=quality,
            fmt=fmt,
            subtitle=subtitle,
            subtitle_lang=subtitle_lang,
            audio_track=audio_track,
            frame_rate=frame_rate,
            codec=codec,
        )
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_finished)
        worker.error.connect(self._on_error)
        self._workers[video_info.video_id] = worker
        worker.start()

    def _process_queue(self):
        max_concurrent = self._settings.concurrent_downloads
        while self._download_queue and len(self._workers) < max_concurrent:
            params = self._download_queue.popleft()
            self._launch_worker(
                params.video_info, params.save_dir, params.download_type,
                params.quality, params.fmt, params.subtitle,
                params.subtitle_lang, params.audio_track,
                params.frame_rate, params.codec,
            )

    def _on_progress(self, video_id: str, data: dict):
        self.download_progress.emit(video_id, data)

    def _on_finished(self, video_id: str, file_path: str):
        self._workers.pop(video_id, None)
        self.download_finished.emit(video_id, file_path)
        self._process_queue()
        self._emit_status()

    def _on_error(self, video_id: str, msg: str):
        self._workers.pop(video_id, None)
        self.download_error.emit(video_id, msg)
        self._process_queue()
        self._emit_status()

    def _emit_status(self):
        active = len(self._workers)
        queued = len(self._download_queue)
        if active > 0:
            msg = f"다운로드 중... ({active}개 진행"
            if queued > 0:
                msg += f", {queued}개 대기"
            msg += ")"
            self.status_message.emit(msg)
        elif queued == 0:
            self.status_message.emit("모든 다운로드 완료")


class _DownloadParams:
    """Bundle of parameters for a queued download."""
    __slots__ = ("video_info", "save_dir", "download_type", "quality", "fmt",
                 "subtitle", "subtitle_lang", "audio_track", "frame_rate", "codec")

    def __init__(self, video_info, save_dir, download_type, quality, fmt,
                 subtitle, subtitle_lang, audio_track, frame_rate, codec):
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
