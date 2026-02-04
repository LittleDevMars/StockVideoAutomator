import os
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFileDialog, QMenu,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction, QIcon

from app.utils.settings_manager import SettingsManager


class ToolBar(QWidget):
    """Top toolbar with paste button, format/quality selectors, save path."""

    paste_clicked = pyqtSignal()
    download_type_changed = pyqtSignal(str)   # "video" or "audio"
    quality_changed = pyqtSignal(str)
    format_changed = pyqtSignal(str)
    save_path_changed = pyqtSignal(str)

    VIDEO_QUALITIES = [
        ("최고", "best"), ("UHD 8K", "4320p"), ("HD 4K", "2160p"),
        ("HQ 2K", "1440p"), ("1080p", "1080p"), ("720p", "720p"),
        ("480p", "480p"), ("360p", "360p"), ("240p", "240p"), ("QCIF", "144p"),
    ]
    FRAME_RATES = ["최고", "60fps", "30fps", "24fps"]
    CODECS = ["H264", "H265", "VP9", "AV1"]
    VR_OPTIONS = ["모든", "360°", "180°"]
    VIDEO_FORMATS = ["자동", "MKV", "MP4"]
    AUDIO_FORMATS = ["자동", "MP3", "M4A", "WAV", "FLAC"]
    PLATFORM_PRESETS = ["Windows", "Mac OS", "Linux", "iOS", "Android"]

    SUBTITLE_LANGS = ["한국어", "English", "日本語", "中文"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = SettingsManager()
        self._save_path = self._settings.default_save_path
        os.makedirs(self._save_path, exist_ok=True)
        self._download_type = self._settings.toolbar_download_type
        self._quality = self._settings.toolbar_quality
        self._quality_label = self._settings.toolbar_quality_label
        self._frame_rate = self._settings.toolbar_frame_rate
        self._codec = self._settings.toolbar_codec
        self._vr = "모든"
        self._format = self._settings.toolbar_format
        self._format_label = self._settings.toolbar_format_label
        self._subtitle_enabled = self._settings.toolbar_subtitle_enabled
        self._subtitle_lang = self._settings.toolbar_subtitle_lang
        self._audio_track = self._settings.toolbar_audio_track
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # Paste link button
        self.btn_paste = QPushButton("  링크 붙여넣기")
        self.btn_paste.setObjectName("pasteButton")
        self.btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste.setMinimumHeight(36)
        layout.addWidget(self.btn_paste)

        layout.addSpacing(8)

        # Download type menu button (replaces QComboBox)
        lbl_type = QLabel("다운로드")
        lbl_type.setObjectName("toolbarLabel")
        layout.addWidget(lbl_type)

        type_label = "비디오" if self._download_type == "video" else "오디오"
        self.btn_download_type = QPushButton(f"{type_label}  ▾")
        self.btn_download_type.setObjectName("downloadTypeButton")
        self.btn_download_type.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download_type.setMinimumHeight(32)
        self.btn_download_type.setMinimumWidth(130)
        self._build_type_menu()
        layout.addWidget(self.btn_download_type)

        # Quality menu button
        lbl_quality = QLabel("화질")
        lbl_quality.setObjectName("toolbarLabel")
        layout.addWidget(lbl_quality)

        self.btn_quality = QPushButton(f"{self._quality_label}  ▾")
        self.btn_quality.setObjectName("qualityButton")
        self.btn_quality.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quality.setMinimumHeight(32)
        self.btn_quality.setMinimumWidth(100)
        self.btn_quality.setEnabled(self._download_type == "video")
        self._build_quality_menu()
        layout.addWidget(self.btn_quality)

        # Format menu button
        lbl_format = QLabel("포맷")
        lbl_format.setObjectName("toolbarLabel")
        layout.addWidget(lbl_format)

        self.btn_format = QPushButton(f"{self._format_label}  ▾")
        self.btn_format.setObjectName("formatButton")
        self.btn_format.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_format.setMinimumHeight(32)
        self.btn_format.setMinimumWidth(90)
        self._build_format_menu()
        layout.addWidget(self.btn_format)

        # Save path menu button
        lbl_save = QLabel("저장하여")
        lbl_save.setObjectName("toolbarLabel")
        layout.addWidget(lbl_save)

        self.btn_save_path = QPushButton(self._get_display_path() + "  ▾")
        self.btn_save_path.setObjectName("savePathButton")
        self.btn_save_path.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_path.setMinimumHeight(32)
        self._build_save_path_menu()
        layout.addWidget(self.btn_save_path)

        layout.addStretch()

    def _build_type_menu(self):
        """Build the download type dropdown menu."""
        menu = QMenu(self)
        menu.setObjectName("downloadTypeMenu")

        # 비디오
        self.act_video = QAction("비디오", self)
        self.act_video.setCheckable(True)
        self.act_video.setChecked(self._download_type == "video")
        self.act_video.triggered.connect(lambda: self._set_download_type("video"))
        menu.addAction(self.act_video)

        # 오디오
        self.act_audio = QAction("오디오", self)
        self.act_audio.setCheckable(True)
        self.act_audio.setChecked(self._download_type == "audio")
        self.act_audio.triggered.connect(lambda: self._set_download_type("audio"))
        menu.addAction(self.act_audio)

        menu.addSeparator()

        # 자막 서브메뉴
        self.subtitle_menu = QMenu("자막", self)
        self.subtitle_menu.setObjectName("downloadTypeMenu")

        self.act_subtitle_off = QAction("사용 안 함", self)
        self.act_subtitle_off.setCheckable(True)
        self.act_subtitle_off.setChecked(not self._subtitle_enabled)
        self.act_subtitle_off.triggered.connect(lambda: self._set_subtitle(False, ""))
        self.subtitle_menu.addAction(self.act_subtitle_off)

        self.subtitle_menu.addSeparator()

        self._subtitle_actions = []  # type: List[QAction]
        for lang in self.SUBTITLE_LANGS:
            act = QAction(lang, self)
            act.setCheckable(True)
            act.setChecked(self._subtitle_enabled and lang == self._subtitle_lang)
            act.triggered.connect(lambda checked, l=lang: self._set_subtitle(True, l))
            self.subtitle_menu.addAction(act)
            self._subtitle_actions.append(act)

        menu.addMenu(self.subtitle_menu)

        # 오디오 트랙 서브메뉴
        self.audio_track_menu = QMenu("오디오 트랙", self)
        self.audio_track_menu.setObjectName("downloadTypeMenu")

        self.act_track_default = QAction("기본", self)
        self.act_track_default.setCheckable(True)
        self.act_track_default.setChecked(self._audio_track == "기본")
        self.act_track_default.triggered.connect(lambda: self._set_audio_track("기본"))
        self.audio_track_menu.addAction(self.act_track_default)

        self.act_track_all = QAction("모든 트랙", self)
        self.act_track_all.setCheckable(True)
        self.act_track_all.setChecked(self._audio_track == "모든 트랙")
        self.act_track_all.triggered.connect(lambda: self._set_audio_track("모든 트랙"))
        self.audio_track_menu.addAction(self.act_track_all)

        menu.addMenu(self.audio_track_menu)

        self.btn_download_type.setMenu(menu)

    def _build_quality_menu(self):
        """Build the quality dropdown menu."""
        menu = QMenu(self)
        menu.setObjectName("downloadTypeMenu")

        # Quality options
        self._quality_actions = []  # type: List[QAction]
        for label, value in self.VIDEO_QUALITIES:
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(value == self._quality)
            act.triggered.connect(
                lambda checked, l=label, v=value: self._set_quality(l, v)
            )
            menu.addAction(act)
            self._quality_actions.append(act)

        menu.addSeparator()

        # 프레임 속도 서브메뉴
        fps_menu = QMenu("프레임 속도", self)
        fps_menu.setObjectName("downloadTypeMenu")
        self._fps_actions = []  # type: List[QAction]
        for fps in self.FRAME_RATES:
            act = QAction(fps, self)
            act.setCheckable(True)
            act.setChecked(fps == self._frame_rate)
            act.triggered.connect(lambda checked, f=fps: self._set_frame_rate(f))
            fps_menu.addAction(act)
            self._fps_actions.append(act)
        menu.addMenu(fps_menu)

        # 코덱 서브메뉴
        codec_menu = QMenu("코덱", self)
        codec_menu.setObjectName("downloadTypeMenu")
        self._codec_actions = []  # type: List[QAction]
        for codec in self.CODECS:
            act = QAction(codec, self)
            act.setCheckable(True)
            act.setChecked(codec == self._codec)
            act.triggered.connect(lambda checked, c=codec: self._set_codec(c))
            codec_menu.addAction(act)
            self._codec_actions.append(act)
        menu.addMenu(codec_menu)

        # VR 서브메뉴
        vr_menu = QMenu("VR", self)
        vr_menu.setObjectName("downloadTypeMenu")
        self._vr_actions = []  # type: List[QAction]
        for vr in self.VR_OPTIONS:
            act = QAction(vr, self)
            act.setCheckable(True)
            act.setChecked(vr == "모든")
            act.triggered.connect(lambda checked, v=vr: self._set_vr(v))
            vr_menu.addAction(act)
            self._vr_actions.append(act)
        menu.addMenu(vr_menu)

        self.btn_quality.setMenu(menu)

    def _set_quality(self, label: str, value: str):
        self._quality = value
        self._quality_label = label
        self.btn_quality.setText(f"{label}  ▾")
        for act in self._quality_actions:
            act.setChecked(act.text() == label)
        self._settings.toolbar_quality = value
        self._settings.toolbar_quality_label = label
        self._settings.sync()
        self.quality_changed.emit(value)

    def _set_frame_rate(self, fps: str):
        self._frame_rate = fps
        for act in self._fps_actions:
            act.setChecked(act.text() == fps)
        self._settings.toolbar_frame_rate = fps
        self._settings.sync()

    def _set_codec(self, codec: str):
        self._codec = codec
        for act in self._codec_actions:
            act.setChecked(act.text() == codec)
        self._settings.toolbar_codec = codec
        self._settings.sync()

    def _set_vr(self, vr: str):
        self._vr = vr
        for act in self._vr_actions:
            act.setChecked(act.text() == vr)

    def _build_format_menu(self):
        """Build the format dropdown menu."""
        menu = QMenu(self)
        menu.setObjectName("downloadTypeMenu")

        formats = self.VIDEO_FORMATS if self._download_type == "video" else self.AUDIO_FORMATS

        self._format_actions = []  # type: List[QAction]
        for fmt in formats:
            act = QAction(fmt, self)
            act.setCheckable(True)
            act.setChecked(fmt == self._format_label)
            act.triggered.connect(lambda checked, f=fmt: self._set_format(f))
            menu.addAction(act)
            self._format_actions.append(act)

        menu.addSeparator()

        # Platform presets
        self._platform_actions = []  # type: List[QAction]
        for platform in self.PLATFORM_PRESETS:
            act = QAction(platform, self)
            act.triggered.connect(lambda checked, p=platform: self._apply_platform_preset(p))
            menu.addAction(act)
            self._platform_actions.append(act)

        self.btn_format.setMenu(menu)

    def _set_format(self, fmt: str):
        if fmt == "자동":
            if self._download_type == "video":
                self._format = "mp4"
            else:
                self._format = "mp3"
            self._format_label = "자동"
        else:
            self._format = fmt.lower()
            self._format_label = fmt

        self.btn_format.setText(f"{self._format_label}  ▾")

        for act in self._format_actions:
            act.setChecked(act.text() == fmt)

        self._settings.toolbar_format = self._format
        self._settings.toolbar_format_label = self._format_label
        self._settings.sync()
        self.format_changed.emit(self._format)

    def _apply_platform_preset(self, platform: str):
        """Apply platform-specific format presets."""
        preset_map = {
            "Windows": ("mp4", "MP4"),
            "Mac OS": ("mp4", "MP4"),
            "Linux": ("mkv", "MKV"),
            "iOS": ("mp4", "MP4"),
            "Android": ("mp4", "MP4"),
        }
        fmt, label = preset_map.get(platform, ("mp4", "MP4"))
        self._format = fmt
        self._format_label = label
        self.btn_format.setText(f"{label}  ▾")

        for act in self._format_actions:
            act.setChecked(act.text() == label)

        self._settings.toolbar_format = self._format
        self._settings.toolbar_format_label = self._format_label
        self._settings.sync()
        self.format_changed.emit(self._format)

    def _rebuild_format_menu(self):
        """Rebuild format menu when download type changes."""
        old_menu = self.btn_format.menu()
        if old_menu:
            old_menu.deleteLater()
        self._build_format_menu()

    def _build_save_path_menu(self):
        """Build the save path dropdown menu."""
        menu = QMenu(self)
        menu.setObjectName("downloadTypeMenu")

        home = os.path.expanduser("~")
        self._path_presets = [
            ("Videos", os.path.join(home, "Videos")),
            ("Downloads", os.path.join(home, "Downloads")),
            ("Pictures", os.path.join(home, "Pictures")),
            ("Documents", os.path.join(home, "Documents")),
        ]

        self._path_actions = []  # type: List[QAction]
        for label, path in self._path_presets:
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(os.path.normpath(path) == os.path.normpath(self._save_path))
            act.triggered.connect(lambda checked, p=path, l=label: self._set_save_path(p, l))
            menu.addAction(act)
            self._path_actions.append(act)

        menu.addSeparator()

        act_browse = QAction("탐색...", self)
        act_browse.triggered.connect(self._select_save_path)
        menu.addAction(act_browse)

        self.btn_save_path.setMenu(menu)

    def _set_save_path(self, path: str, label: str):
        os.makedirs(path, exist_ok=True)
        self._save_path = path
        self.btn_save_path.setText(f"{label}  ▾")

        for act in self._path_actions:
            act.setChecked(act.text() == label)

        self.save_path_changed.emit(path)

    def _set_download_type(self, dtype: str):
        self._download_type = dtype
        is_video = dtype == "video"

        # Update check marks
        self.act_video.setChecked(is_video)
        self.act_audio.setChecked(not is_video)

        # Update button text
        label = "비디오" if is_video else "오디오"
        self.btn_download_type.setText(f"{label}  ▾")

        # Update format menu and quality button
        if is_video:
            self._format = "mp4"
            self._format_label = "MP4"
            self.btn_quality.setEnabled(True)
        else:
            self._format = "mp3"
            self._format_label = "MP3"
            self.btn_quality.setEnabled(False)
        self.btn_format.setText(f"{self._format_label}  ▾")
        self._rebuild_format_menu()

        self._settings.toolbar_download_type = self._download_type
        self._settings.toolbar_format = self._format
        self._settings.toolbar_format_label = self._format_label
        self._settings.sync()
        self.download_type_changed.emit(dtype)

    def _set_subtitle(self, enabled: bool, lang: str):
        self._subtitle_enabled = enabled
        self._subtitle_lang = lang

        # Update check marks
        self.act_subtitle_off.setChecked(not enabled)
        for act in self._subtitle_actions:
            act.setChecked(enabled and act.text() == lang)

        self._settings.toolbar_subtitle_enabled = enabled
        self._settings.toolbar_subtitle_lang = lang
        self._settings.sync()

    def _set_audio_track(self, track: str):
        self._audio_track = track
        self.act_track_default.setChecked(track == "기본")
        self.act_track_all.setChecked(track == "모든 트랙")
        self._settings.toolbar_audio_track = track
        self._settings.sync()

    def _connect_signals(self):
        self.btn_paste.clicked.connect(self.paste_clicked.emit)

    def _select_save_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "저장 폴더 선택", self._save_path
        )
        if path:
            self._save_path = path
            display = self._get_display_path()
            self.btn_save_path.setText(f"{display}  ▾")

            # Update check marks - check if it matches a preset
            norm_path = os.path.normpath(path)
            for i, act in enumerate(self._path_actions):
                _, preset_path = self._path_presets[i]
                act.setChecked(os.path.normpath(preset_path) == norm_path)

            self.save_path_changed.emit(path)

    def _get_display_path(self) -> str:
        name = os.path.basename(self._save_path)
        return name if name else self._save_path

    @property
    def save_path(self) -> str:
        return self._save_path

    @property
    def download_type(self) -> str:
        return self._download_type

    @property
    def quality(self) -> str:
        return self._quality

    @property
    def format(self) -> str:
        return self._format

    @property
    def subtitle_enabled(self) -> bool:
        return self._subtitle_enabled

    @property
    def subtitle_lang(self) -> str:
        return self._subtitle_lang

    @property
    def audio_track(self) -> str:
        return self._audio_track

    @property
    def frame_rate(self) -> str:
        return self._frame_rate

    @property
    def codec(self) -> str:
        return self._codec
