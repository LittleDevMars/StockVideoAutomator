import os
import subprocess
import sys
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPushButton,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl, QThread
from PyQt6.QtGui import QPixmap, QDesktopServices, QMouseEvent

from app.models.video_info import VideoInfo
from app.utils.helpers import format_duration, format_file_size, format_speed


class _ThumbnailLoader(QThread):
    """Background thread to download a thumbnail image."""

    loaded = pyqtSignal(bytes)  # raw image data
    failed = pyqtSignal()

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self):
        try:
            import requests
            resp = requests.get(self._url, timeout=5)
            if resp.status_code == 200:
                self.loaded.emit(resp.content)
            else:
                self.failed.emit()
        except Exception:
            self.failed.emit()


class DownloadItemWidget(QWidget):
    """Single download item widget showing thumbnail, info, progress."""

    cancel_requested = pyqtSignal(str)  # video_id
    remove_requested = pyqtSignal(str)  # video_id
    clicked = pyqtSignal(str)  # video_id — for selection management

    def __init__(self, video_info: VideoInfo, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self._selected = False
        self._setup_ui()
        self._load_thumbnail()

    def _setup_ui(self):
        self.setObjectName("downloadItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(70)
        self.setMaximumHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Thumbnail
        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setFixedSize(QSize(100, 56))
        self.lbl_thumbnail.setObjectName("thumbnail")
        self.lbl_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_thumbnail.setScaledContents(True)
        self.lbl_thumbnail.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_thumbnail)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.lbl_title = QLabel(self.video_info.title)
        self.lbl_title.setObjectName("itemTitle")
        self.lbl_title.setWordWrap(False)
        self.lbl_title.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.lbl_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        info_layout.addWidget(self.lbl_title)

        # Meta info: duration · size · format · resolution · fps · channel
        meta_parts = []
        if self.video_info.duration:
            meta_parts.append(format_duration(self.video_info.duration))
        if self.video_info.filesize_approx:
            meta_parts.append(format_file_size(self.video_info.filesize_approx))
        if self.video_info.ext:
            meta_parts.append(self.video_info.ext.upper())
        if self.video_info.resolution:
            meta_parts.append(self.video_info.resolution)
        if self.video_info.fps:
            meta_parts.append(f"{self.video_info.fps}fps")
        if self.video_info.channel:
            meta_parts.append(self.video_info.channel)

        meta_text = " · ".join(meta_parts) if meta_parts else ""
        self.lbl_meta = QLabel(meta_text)
        self.lbl_meta.setObjectName("itemMeta")
        self.lbl_meta.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        info_layout.addWidget(self.lbl_meta)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("itemProgress")
        self.progress_bar.setMaximumHeight(14)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        info_layout.addWidget(self.progress_bar)

        layout.addLayout(info_layout, stretch=1)

        # Status / Speed label
        self.lbl_status = QLabel("대기중")
        self.lbl_status.setObjectName("itemStatus")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_status.setMinimumWidth(100)
        self.lbl_status.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_status)

        # Open folder button
        self.btn_folder = QPushButton("📂")
        self.btn_folder.setObjectName("itemFolderButton")
        self.btn_folder.setFixedSize(28, 28)
        self.btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_folder.setToolTip("저장 폴더 열기")
        self.btn_folder.clicked.connect(self._on_open_folder)
        self.btn_folder.setVisible(False)
        layout.addWidget(self.btn_folder)

        # Cancel / Remove button
        self.btn_action = QPushButton("✕")
        self.btn_action.setObjectName("itemActionButton")
        self.btn_action.setFixedSize(28, 28)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self._on_action)
        layout.addWidget(self.btn_action)

    def _load_thumbnail(self):
        if not self.video_info.thumbnail_url:
            self.lbl_thumbnail.setText("No Image")
            return
        self.lbl_thumbnail.setText("...")
        self._thumb_loader = _ThumbnailLoader(self.video_info.thumbnail_url, self)
        self._thumb_loader.loaded.connect(self._on_thumbnail_loaded)
        self._thumb_loader.failed.connect(self._on_thumbnail_failed)
        self._thumb_loader.start()

    def _on_thumbnail_loaded(self, data: bytes):
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        self.lbl_thumbnail.setPixmap(
            pixmap.scaled(
                100, 56,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _on_thumbnail_failed(self):
        self.lbl_thumbnail.setText("No Image")

    def update_progress(self, data: dict):
        status = data.get("status", "")

        if status == "downloading":
            pct = data.get("progress", 0)
            speed = data.get("speed", 0)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(int(pct))
            self.lbl_status.setText(format_speed(speed))
            self.video_info.status = "downloading"
            self.video_info.progress = pct
            self.video_info.speed = speed

        elif status == "processing":
            self.progress_bar.setValue(100)
            self.lbl_status.setText("변환 중...")

    def set_completed(self, file_path: str):
        self.video_info.status = "completed"
        self.video_info.downloaded_path = file_path
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("완료")
        self.lbl_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.btn_action.setText("✕")
        self.btn_folder.setVisible(True)

    def set_error(self, msg: str):
        self.video_info.status = "error"
        self.video_info.error_message = msg
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("오류")
        self.lbl_status.setStyleSheet("color: #f44336; font-weight: bold;")

    # -- Selection -----------------------------------------------------------

    def set_selected(self, selected: bool):
        self._selected = selected
        # QSS [selected="true"] matches string, not bool
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    @property
    def is_selected(self) -> bool:
        return self._selected

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit(self.video_info.video_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if (self.video_info.status == "completed"
                and self.video_info.downloaded_path
                and os.path.isfile(self.video_info.downloaded_path)):
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(self.video_info.downloaded_path)
            )
        else:
            super().mouseDoubleClickEvent(event)

    # -- Actions --------------------------------------------------------------

    def _on_open_folder(self):
        path = self.video_info.downloaded_path
        if path and os.path.exists(path):
            folder = os.path.dirname(path)
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _on_action(self):
        if self.video_info.status == "downloading":
            self.cancel_requested.emit(self.video_info.video_id)
        else:
            self.remove_requested.emit(self.video_info.video_id)
