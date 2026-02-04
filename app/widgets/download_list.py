from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.models.video_info import VideoInfo
from app.widgets.download_item import DownloadItemWidget


class DownloadList(QWidget):
    """Scrollable list of download items."""

    cancel_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    count_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: Dict[str, DownloadItemWidget] = {}
        self._selected_id: Optional[str] = None
        self._add_counter: int = 0
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("downloadScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Container inside scroll
        self.container = QWidget()
        self.container.setObjectName("downloadContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(1)
        self.container_layout.addStretch()

        # Empty placeholder
        self.lbl_empty = QLabel("링크를 붙여넣어 다운로드를 시작하세요")
        self.lbl_empty.setObjectName("emptyLabel")
        self.lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.lbl_empty.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.container_layout.insertWidget(0, self.lbl_empty)

        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

    def add_item(self, video_info: VideoInfo) -> DownloadItemWidget:
        self.lbl_empty.hide()

        # 추가 순서 기록
        self._add_counter += 1
        video_info.added_index = self._add_counter

        # Remove existing widget with same video_id to prevent orphans
        vid = video_info.video_id
        old_widget = self._items.pop(vid, None)
        if old_widget:
            self.container_layout.removeWidget(old_widget)
            old_widget.deleteLater()

        widget = DownloadItemWidget(video_info)
        widget.cancel_requested.connect(self.cancel_requested.emit)
        widget.remove_requested.connect(self._remove_item)
        widget.clicked.connect(self._select_item)

        # Insert before the stretch
        count = self.container_layout.count()
        self.container_layout.insertWidget(count - 1, widget)
        self._items[vid] = widget
        self.count_changed.emit(len(self._items))
        return widget

    def get_item(self, video_id: str) -> Optional[DownloadItemWidget]:
        return self._items.get(video_id)

    def _select_item(self, video_id: str):
        # Deselect previous
        if self._selected_id and self._selected_id in self._items:
            self._items[self._selected_id].set_selected(False)
        # Select new
        self._selected_id = video_id
        if video_id in self._items:
            self._items[video_id].set_selected(True)

    def _remove_item(self, video_id: str):
        if self._selected_id == video_id:
            self._selected_id = None
        widget = self._items.pop(video_id, None)
        if widget:
            self.container_layout.removeWidget(widget)
            widget.deleteLater()
            self.count_changed.emit(len(self._items))

            if not self._items:
                self.lbl_empty.setVisible(True)

        self.remove_requested.emit(video_id)

    def get_items_by_type(self, download_type: str) -> List[DownloadItemWidget]:
        """Filter items by download type."""
        return [
            w for w in self._items.values()
            if w.video_info.download_type == download_type
        ]

    def get_playlist_items(self) -> List[DownloadItemWidget]:
        return [
            w for w in self._items.values()
            if w.video_info.is_playlist
        ]

    def get_all_items(self) -> List[DownloadItemWidget]:
        return list(self._items.values())

    def sort_items(self, key: str, ascending: bool = True):
        """Sort download items by the given key."""
        widgets = list(self._items.values())
        reverse = not ascending

        if key == "name":
            widgets.sort(key=lambda w: w.video_info.title.lower(), reverse=reverse)
        elif key == "size":
            widgets.sort(key=lambda w: w.video_info.filesize_approx or 0, reverse=reverse)
        elif key == "status":
            order = {"downloading": 0, "processing": 1, "queued": 2,
                     "paused": 3, "completed": 4, "error": 5}
            widgets.sort(key=lambda w: order.get(w.video_info.status, 9), reverse=reverse)
        else:  # "added" - 추가순 (기본)
            widgets.sort(key=lambda w: w.video_info.added_index, reverse=reverse)

        # 레이아웃에서 위젯 재배치 (stretch 앞에 삽입)
        for w in widgets:
            self.container_layout.removeWidget(w)
        for i, w in enumerate(widgets):
            self.container_layout.insertWidget(i, w)

    @property
    def item_count(self) -> int:
        return len(self._items)
