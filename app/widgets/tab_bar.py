from typing import Dict
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QLineEdit, QMenu,
)
from PyQt6.QtCore import pyqtSignal, Qt, QEvent, QTimer
from PyQt6.QtGui import QAction


class TabBar(QWidget):
    """Tab bar: 전체 / 동영상 / 오디오 / 재생 목록  +  search filter"""

    tab_changed = pyqtSignal(str)
    search_changed = pyqtSignal(str)  # emitted when filter text changes
    sort_changed = pyqtSignal(str, bool)  # key, ascending

    TABS = ["전체", "동영상", "오디오", "재생 목록"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_tab = "전체"
        self._buttons: Dict[str, QPushButton] = {}
        self._search_visible = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(0)

        for tab_name in self.TABS:
            btn = QPushButton(tab_name)
            btn.setObjectName("tabButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(32)
            btn.setMinimumWidth(80)
            if tab_name == "전체":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, name=tab_name: self._on_tab_click(name))
            layout.addWidget(btn)
            self._buttons[tab_name] = btn

        layout.addStretch()

        # Item count label (visible when search is hidden)
        self.lbl_count = QLabel("0 아이템")
        self.lbl_count.setObjectName("countLabel")
        layout.addWidget(self.lbl_count)

        # Search filter toggle button
        self.btn_search = QPushButton("🔍")
        self.btn_search.setObjectName("tabSearchButton")
        self.btn_search.setFixedSize(32, 32)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.setToolTip("필터 상자 표시")
        self.btn_search.clicked.connect(self._toggle_search)
        layout.addWidget(self.btn_search)

        # Search input field (hidden by default)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("tabSearchInput")
        self.search_input.setPlaceholderText("다운로드한 항목 중에서 검색")
        self.search_input.setFixedHeight(30)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setVisible(False)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.installEventFilter(self)
        layout.addWidget(self.search_input)

        # Sort button
        self.btn_sort = QPushButton("↕")
        self.btn_sort.setObjectName("tabSortButton")
        self.btn_sort.setFixedSize(32, 32)
        self.btn_sort.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sort.setToolTip("정렬")
        self._build_sort_menu()
        layout.addWidget(self.btn_sort)

    def _on_tab_click(self, name: str):
        self._current_tab = name
        for tab_name, btn in self._buttons.items():
            btn.setChecked(tab_name == name)
        self.tab_changed.emit(name)

    def _toggle_search(self):
        self._search_visible = not self._search_visible
        self.search_input.setVisible(self._search_visible)
        self.lbl_count.setVisible(not self._search_visible)

        if self._search_visible:
            self.search_input.setFocus()
            self.btn_search.setToolTip("필터 상자 숨기기")
        else:
            self.search_input.clear()
            self.btn_search.setToolTip("필터 상자 표시")

    def eventFilter(self, obj, event):
        if obj is self.search_input and event.type() == QEvent.Type.FocusOut:
            # Delay check so the new focus target is resolved
            QTimer.singleShot(0, self._check_close_search)
        return super().eventFilter(obj, event)

    def _check_close_search(self):
        """Close search bar if focus moved outside search-related widgets."""
        if not self._search_visible:
            return
        from PyQt6.QtWidgets import QApplication
        focused = QApplication.focusWidget()
        # Keep open if focus is still on the input or the toggle button
        if focused is self.search_input or focused is self.btn_search:
            return
        self._close_search()

    def _close_search(self):
        if not self._search_visible:
            return
        self._search_visible = False
        self.search_input.setVisible(False)
        self.lbl_count.setVisible(True)
        self.search_input.clear()
        self.btn_search.setToolTip("필터 상자 표시")

    def _on_search_text_changed(self, text: str):
        self.search_changed.emit(text)

    def _build_sort_menu(self):
        self._sort_key = "added"
        self._sort_ascending = True

        menu = QMenu(self)
        menu.setObjectName("downloadTypeMenu")
        sort_options = [
            ("추가순", "added"),
            ("이름순", "name"),
            ("크기순", "size"),
            ("상태순", "status"),
        ]
        self._sort_actions = []
        for label, key in sort_options:
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(key == "added")
            act.triggered.connect(lambda checked, k=key: self._on_sort_selected(k))
            menu.addAction(act)
            self._sort_actions.append((act, key))

        menu.addSeparator()

        self.act_asc = QAction("오름차순 ↑", self)
        self.act_asc.setCheckable(True)
        self.act_asc.setChecked(True)
        self.act_asc.triggered.connect(lambda: self._on_order_selected(True))
        menu.addAction(self.act_asc)

        self.act_desc = QAction("내림차순 ↓", self)
        self.act_desc.setCheckable(True)
        self.act_desc.setChecked(False)
        self.act_desc.triggered.connect(lambda: self._on_order_selected(False))
        menu.addAction(self.act_desc)

        self.btn_sort.setMenu(menu)

    def _on_sort_selected(self, key: str):
        self._sort_key = key
        for act, k in self._sort_actions:
            act.setChecked(k == key)
        self.sort_changed.emit(self._sort_key, self._sort_ascending)

    def _on_order_selected(self, ascending: bool):
        self._sort_ascending = ascending
        self.act_asc.setChecked(ascending)
        self.act_desc.setChecked(not ascending)
        self.sort_changed.emit(self._sort_key, self._sort_ascending)

    def set_count(self, count: int):
        self.lbl_count.setText(f"{count} 아이템")

    @property
    def current_tab(self) -> str:
        return self._current_tab
