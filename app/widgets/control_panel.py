from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QMouseEvent


class ControlPanelOverlay(QWidget):
    """Transparent overlay behind the control panel. Clicking it closes the panel."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cpOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 80);")

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit()
        super().mousePressEvent(event)


class ControlPanelItem(QWidget):
    """Single clickable menu item in the control panel."""

    clicked = pyqtSignal()

    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("controlPanelItem")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        lbl_icon = QLabel(icon_text)
        lbl_icon.setObjectName("cpItemIcon")
        lbl_icon.setFixedWidth(24)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(lbl_icon)

        lbl_text = QLabel(label)
        lbl_text.setObjectName("cpItemText")
        lbl_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(lbl_text, stretch=1)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class ControlPanel(QWidget):
    """Right-side sliding control panel (4K Video Downloader+ style)."""

    preferences_requested = pyqtSignal()
    login_requested = pyqtSignal()
    liked_download_requested = pyqtSignal()
    watch_later_requested = pyqtSignal()
    license_requested = pyqtSignal()
    support_requested = pyqtSignal()

    PANEL_WIDTH = 320

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(self.PANEL_WIDTH)
        self._is_open = False

        # Overlay (created as sibling, behind the panel)
        self._overlay = ControlPanelOverlay(parent)
        self._overlay.setVisible(False)
        self._overlay.clicked.connect(self.close_panel)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header ───────────────────────────────────
        header = QWidget()
        header.setObjectName("cpHeader")
        header.setFixedHeight(50)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 8, 0)

        lbl_title = QLabel("제어판")
        lbl_title.setObjectName("cpTitle")
        font = lbl_title.font()
        font.setPointSize(13)
        font.setBold(True)
        lbl_title.setFont(font)
        header_layout.addWidget(lbl_title)

        header_layout.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setObjectName("cpCloseButton")
        btn_close.setFixedSize(32, 32)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.toggle)
        header_layout.addWidget(btn_close)

        main_layout.addWidget(header)

        # ── Separator ────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("cpSeparator")
        main_layout.addWidget(sep)

        # ── Scroll area for content ──────────────────
        scroll = QScrollArea()
        scroll.setObjectName("cpScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()
        content.setObjectName("cpContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 8, 0, 8)
        content_layout.setSpacing(0)

        # ── YouTube Login section ────────────────────
        login_section = QWidget()
        login_section.setObjectName("cpLoginSection")
        login_layout = QVBoxLayout(login_section)
        login_layout.setContentsMargins(16, 12, 16, 12)
        login_layout.setSpacing(8)

        yt_label = QLabel("YouTube")
        yt_label.setObjectName("cpYoutubeLabel")
        yt_font = yt_label.font()
        yt_font.setPointSize(14)
        yt_font.setBold(True)
        yt_label.setFont(yt_font)
        login_layout.addWidget(yt_label)

        login_desc = QLabel("YouTube 계정으로 로그인하여\n개인 재생목록에 접근하세요.")
        login_desc.setObjectName("cpLoginDesc")
        login_desc.setWordWrap(True)
        login_layout.addWidget(login_desc)

        btn_login = QPushButton("로그인")
        btn_login.setObjectName("cpLoginButton")
        btn_login.setFixedHeight(36)
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self.login_requested.emit)
        login_layout.addWidget(btn_login)

        content_layout.addWidget(login_section)

        # ── Separator ────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setObjectName("cpSeparator")
        content_layout.addWidget(sep2)

        # ── Menu items ───────────────────────────────
        item_prefs = ControlPanelItem("⚙", "환경설정")
        item_prefs.clicked.connect(self.preferences_requested.emit)
        content_layout.addWidget(item_prefs)

        item_liked = ControlPanelItem("👍", '"좋아요 표시" 다운로드')
        item_liked.clicked.connect(self.liked_download_requested.emit)
        content_layout.addWidget(item_liked)

        item_watch = ControlPanelItem("🕐", '"나중에 볼" 다운로드')
        item_watch.clicked.connect(self.watch_later_requested.emit)
        content_layout.addWidget(item_watch)

        item_license = ControlPanelItem("🔑", "활성화")
        item_license.clicked.connect(self.license_requested.emit)
        content_layout.addWidget(item_license)

        item_support = ControlPanelItem("💬", "지원 받기")
        item_support.clicked.connect(self.support_requested.emit)
        content_layout.addWidget(item_support)

        # ── Separator ────────────────────────────────
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setObjectName("cpSeparator")
        content_layout.addWidget(sep3)

        # ── News section ─────────────────────────────
        news_section = QWidget()
        news_section.setObjectName("cpNewsSection")
        news_layout = QVBoxLayout(news_section)
        news_layout.setContentsMargins(16, 12, 16, 12)
        news_layout.setSpacing(8)

        news_title = QLabel("뉴스")
        news_title.setObjectName("cpNewsTitle")
        nf = news_title.font()
        nf.setPointSize(12)
        nf.setBold(True)
        news_title.setFont(nf)
        news_layout.addWidget(news_title)

        news_body = QLabel("새로운 소식이 없습니다.")
        news_body.setObjectName("cpNewsBody")
        news_body.setWordWrap(True)
        news_layout.addWidget(news_body)

        content_layout.addWidget(news_section)

        # ── Separator ────────────────────────────────
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.Shape.HLine)
        sep4.setObjectName("cpSeparator")
        content_layout.addWidget(sep4)

        # ── Download notifications section ───────────
        notif_section = QWidget()
        notif_section.setObjectName("cpNotifSection")
        notif_layout = QVBoxLayout(notif_section)
        notif_layout.setContentsMargins(16, 12, 16, 12)
        notif_layout.setSpacing(8)

        notif_title = QLabel("다운로드 알림")
        notif_title.setObjectName("cpNotifTitle")
        ntf = notif_title.font()
        ntf.setPointSize(12)
        ntf.setBold(True)
        notif_title.setFont(ntf)
        notif_layout.addWidget(notif_title)

        self.lbl_notif_body = QLabel("완료된 다운로드가 없습니다.")
        self.lbl_notif_body.setObjectName("cpNotifBody")
        self.lbl_notif_body.setWordWrap(True)
        notif_layout.addWidget(self.lbl_notif_body)

        content_layout.addWidget(notif_section)

        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll, stretch=1)

    # ── Animation / toggle ───────────────────────────

    def toggle(self):
        if self._is_open:
            self.close_panel()
        else:
            self.open_panel()

    def open_panel(self):
        if self._is_open:
            return
        self._is_open = True

        # Show overlay behind the panel
        parent = self.parent()
        if parent:
            self._overlay.setGeometry(0, 0, parent.width(), parent.height())
            self._overlay.setVisible(True)
            self._overlay.raise_()

        self.setVisible(True)
        self.raise_()
        self._animate(show=True)

    def close_panel(self):
        if not self._is_open:
            return
        self._is_open = False
        self._overlay.setVisible(False)
        self._animate(show=False)

    def _animate(self, show: bool):
        parent = self.parent()
        if not parent:
            return

        parent_width = parent.width()
        panel_w = self.PANEL_WIDTH

        start_x = parent_width if show else parent_width - panel_w
        end_x = parent_width - panel_w if show else parent_width

        self.setGeometry(start_x, self.y(), panel_w, parent.height())

        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(250)
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(
            self.geometry().adjusted(end_x - start_x, 0, end_x - start_x, 0)
        )
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        if not show:
            self._anim.finished.connect(lambda: self.setVisible(False))

        self._anim.start()

    @property
    def is_open(self) -> bool:
        return self._is_open

    def update_notification(self, title: str, message: str):
        self.lbl_notif_body.setText(f"{title}\n{message}")

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def reposition(self, parent_width: int, parent_height: int):
        """Reposition panel and overlay when parent resizes."""
        if self._is_open:
            self._overlay.setGeometry(0, 0, parent_width, parent_height)
            self.setGeometry(
                parent_width - self.PANEL_WIDTH, 0,
                self.PANEL_WIDTH, parent_height,
            )
        else:
            self.setGeometry(
                parent_width, 0,
                self.PANEL_WIDTH, parent_height,
            )
