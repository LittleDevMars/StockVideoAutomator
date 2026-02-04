import os
import sys
from collections import deque
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStatusBar, QApplication,
    QMessageBox, QInputDialog, QMenuBar, QMenu, QFileDialog,
    QSystemTrayIcon,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QDesktopServices, QKeySequence, QIcon

from app.widgets.toolbar import ToolBar
from app.widgets.tab_bar import TabBar
from app.widgets.download_list import DownloadList
from app.widgets.download_item import DownloadItemWidget
from app.widgets.control_panel import ControlPanel
from app.models.video_info import VideoInfo
from app.models.database import DownloadDatabase
from app.utils.helpers import is_youtube_url, resource_path
from app.utils.settings_manager import SettingsManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Video Automator")
        self.setMinimumSize(900, 600)
        self.resize(1000, 650)

        # App icon
        self._ico_path = resource_path("app", "resources", "app_icon.ico")
        self._app_icon = QIcon(self._ico_path)
        if not self._app_icon.isNull():
            self.setWindowIcon(self._app_icon)

        self._settings = SettingsManager()
        self.db = DownloadDatabase()
        self._workers: Dict[str, DownloadWorker] = {}
        self._download_queue: deque = deque()  # queued VideoInfo objects
        self._info_worker: Optional[InfoWorker] = None
        self._update_worker: Optional[YtDlpUpdateWorker] = None
        self._force_quit = False

        self._setup_menubar()
        self._setup_ui()
        self._setup_tray()
        self._connect_signals()
        self._load_stylesheet()
        self._start_bridge_server()

        # 창 표시 후 무거운 작업 지연 실행
        QTimer.singleShot(0, self._load_history)
        QTimer.singleShot(100, self._auto_check_ytdlp_update)
        QTimer.singleShot(200, self._check_dependencies)

    def _setup_menubar(self):
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일")

        act_paste = QAction("링크 붙여넣기", self)
        act_paste.triggered.connect(self._on_paste)
        file_menu.addAction(act_paste)

        file_menu.addSeparator()

        act_save_path = QAction("저장 폴더 변경...", self)
        act_save_path.triggered.connect(self._change_save_path)
        file_menu.addAction(act_save_path)

        act_open_folder = QAction("저장 폴더 열기", self)
        act_open_folder.triggered.connect(self._open_save_folder)
        file_menu.addAction(act_open_folder)

        file_menu.addSeparator()

        act_exit = QAction("종료", self)
        act_exit.setShortcut(QKeySequence("Alt+F4"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # 수정 메뉴
        edit_menu = menubar.addMenu("수정")

        act_paste2 = QAction("링크 붙여넣기...", self)
        act_paste2.setShortcut(QKeySequence("Ctrl+V"))
        act_paste2.triggered.connect(self._on_paste)
        edit_menu.addAction(act_paste2)

        edit_menu.addSeparator()

        # "나중에 볼" 다운로드 서브메뉴
        watch_later_menu = QMenu('"나중에 볼" 다운로드', self)
        act_wl_download = QAction("재생목록 다운로드", self)
        act_wl_download.triggered.connect(lambda: self._download_playlist_type("watch_later"))
        watch_later_menu.addAction(act_wl_download)
        act_wl_subscribe = QAction("재생 목록 구독", self)
        act_wl_subscribe.triggered.connect(lambda: self._subscribe_playlist("watch_later"))
        watch_later_menu.addAction(act_wl_subscribe)
        edit_menu.addMenu(watch_later_menu)

        # "좋아요 표시" 다운로드 서브메뉴
        liked_menu = QMenu('"좋아요 표시" 다운로드', self)
        act_liked_download = QAction("재생목록 다운로드", self)
        act_liked_download.triggered.connect(lambda: self._download_playlist_type("liked"))
        liked_menu.addAction(act_liked_download)
        act_liked_subscribe = QAction("재생 목록 구독", self)
        act_liked_subscribe.triggered.connect(lambda: self._subscribe_playlist("liked"))
        liked_menu.addAction(act_liked_subscribe)
        edit_menu.addMenu(liked_menu)

        edit_menu.addSeparator()

        act_pause_all = QAction("모두 일시정지", self)
        act_pause_all.triggered.connect(self._pause_all)
        edit_menu.addAction(act_pause_all)

        act_resume_all = QAction("모두 재시작", self)
        act_resume_all.triggered.connect(self._resume_all)
        edit_menu.addAction(act_resume_all)

        act_remove_all = QAction("모두 제거", self)
        act_remove_all.triggered.connect(self._remove_all)
        edit_menu.addAction(act_remove_all)

        # 보기 메뉴
        view_menu = menubar.addMenu("보기")

        act_all = QAction("전체", self)
        act_all.triggered.connect(lambda: self.tab_bar._on_tab_click("전체"))
        view_menu.addAction(act_all)

        act_video = QAction("동영상", self)
        act_video.triggered.connect(lambda: self.tab_bar._on_tab_click("동영상"))
        view_menu.addAction(act_video)

        act_audio = QAction("오디오", self)
        act_audio.triggered.connect(lambda: self.tab_bar._on_tab_click("오디오"))
        view_menu.addAction(act_audio)

        act_playlist = QAction("재생 목록", self)
        act_playlist.triggered.connect(lambda: self.tab_bar._on_tab_click("재생 목록"))
        view_menu.addAction(act_playlist)

        # 도구 메뉴
        tools_menu = menubar.addMenu("도구")

        act_control_panel = QAction("제어판...", self)
        act_control_panel.triggered.connect(self._show_control_panel)
        tools_menu.addAction(act_control_panel)

        act_preferences = QAction("환경설정...", self)
        act_preferences.triggered.connect(self._show_preferences)
        tools_menu.addAction(act_preferences)

        act_license = QAction("라이센스 관리하기...", self)
        act_license.triggered.connect(self._show_license)
        tools_menu.addAction(act_license)

        act_update = QAction("업데이트 확인...", self)
        act_update.triggered.connect(self._check_update)
        tools_menu.addAction(act_update)

        tools_menu.addSeparator()

        act_ytdlp_update = QAction("yt-dlp 업데이트", self)
        act_ytdlp_update.triggered.connect(self._update_ytdlp)
        tools_menu.addAction(act_ytdlp_update)

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말")

        act_about = QAction("Stock Video Automator 정보", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self.toolbar = ToolBar()
        self.toolbar.setObjectName("toolbar")
        layout.addWidget(self.toolbar)

        # Tab bar
        self.tab_bar = TabBar()
        self.tab_bar.setObjectName("tabBarWidget")
        layout.addWidget(self.tab_bar)

        # Download list
        self.download_list = DownloadList()
        layout.addWidget(self.download_list, stretch=1)

        # Control panel (overlay, right-side)
        self.control_panel = ControlPanel(central)
        self.control_panel.setVisible(False)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비")

    def _setup_tray(self):
        """Initialize system tray icon with context menu."""
        self.tray_icon = QSystemTrayIcon(self)
        if not self._app_icon.isNull():
            self.tray_icon.setIcon(self._app_icon)
        else:
            self.tray_icon.setIcon(self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            ))
        self.tray_icon.setToolTip("Stock Video Automator")

        tray_menu = QMenu(self)
        act_show = QAction("열기", self)
        act_show.triggered.connect(self._tray_show)
        tray_menu.addAction(act_show)

        tray_menu.addSeparator()

        act_quit = QAction("종료", self)
        act_quit.triggered.connect(self._tray_quit)
        tray_menu.addAction(act_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

        if self._settings.run_in_background:
            self.tray_icon.show()

    def _tray_show(self):
        self.showNormal()
        self.activateWindow()

    def _tray_quit(self):
        self._force_quit = True
        self.close()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._tray_show()

    def _connect_signals(self):
        self.toolbar.paste_clicked.connect(self._on_paste)
        self.tab_bar.tab_changed.connect(self._on_tab_changed)
        self.download_list.count_changed.connect(self.tab_bar.set_count)
        self.download_list.cancel_requested.connect(self._cancel_download)

        # Control panel signals
        self.control_panel.preferences_requested.connect(self._show_preferences)
        self.control_panel.login_requested.connect(self._on_youtube_login)
        self.control_panel.liked_download_requested.connect(
            lambda: self._download_playlist_type("liked")
        )
        self.control_panel.watch_later_requested.connect(
            lambda: self._download_playlist_type("watch_later")
        )
        self.control_panel.license_requested.connect(self._show_license)
        self.control_panel.support_requested.connect(self._show_support)

        # Search filter
        self.tab_bar.search_changed.connect(self._on_search_filter)

        # Sort
        self.tab_bar.sort_changed.connect(self.download_list.sort_items)

    def _load_stylesheet(self):
        qss_path = resource_path("app", "resources", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    # ── MCP Bridge Server ─────────────────────────────────────

    def _start_bridge_server(self):
        from app.bridge.bridge_server import BridgeServer
        self._bridge_server = BridgeServer(self, parent=self)
        self._bridge_server.start()

    # ── Dependency check ────────────────────────────────────────

    def _check_dependencies(self):
        from app.utils.dependency_installer import (
            find_ffmpeg, find_deno, add_tools_to_path,
            DependencyInstaller,
        )
        add_tools_to_path()
        need_ffmpeg = find_ffmpeg() is None
        need_deno = find_deno() is None

        if not need_ffmpeg and not need_deno:
            return

        names = []
        if need_ffmpeg:
            names.append("ffmpeg")
        if need_deno:
            names.append("deno")

        reply = QMessageBox.question(
            self, "의존성 설치",
            f"{', '.join(names)}이(가) 설치되어 있지 않습니다.\n"
            "자동으로 다운로드하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._dep_installer = DependencyInstaller(
            install_ffmpeg=need_ffmpeg,
            install_deno=need_deno,
        )
        self._dep_installer.status.connect(self.status_bar.showMessage)
        self._dep_installer.finished.connect(self._on_dep_install_finished)
        self._dep_installer.start()

    def _on_dep_install_finished(self, success: bool, msg: str):
        if success:
            self.status_bar.showMessage(msg, 5000)
        else:
            QMessageBox.warning(self, "의존성 설치 오류", msg)
            self.status_bar.showMessage("의존성 설치 실패", 5000)

    # ── Load history ───────────────────────────────────────────

    def _load_history(self):
        records = self.db.get_all_records()
        for rec in reversed(records):  # oldest first
            vi = VideoInfo(
                url=rec.get("url", ""),
                video_id=rec.get("video_id", ""),
                title=rec.get("title", ""),
                channel=rec.get("channel", ""),
                duration=rec.get("duration") or 0,
                thumbnail_url=rec.get("thumbnail_url", ""),
                filesize_approx=rec.get("filesize") or 0,
                ext=rec.get("format", "mp4"),
                status="completed",
                downloaded_path=rec.get("file_path", ""),
                download_type=rec.get("download_type", "video"),
                selected_quality=rec.get("quality", ""),
            )
            widget = self.download_list.add_item(vi)
            widget.set_completed(vi.downloaded_path)

        count = len(records)
        if count > 0:
            self.status_bar.showMessage(f"이전 다운로드 {count}개 로드됨")

    # ── Paste / URL handling ─────────────────────────────────

    def _on_paste(self):
        clipboard = QApplication.clipboard()
        url = clipboard.text().strip() if clipboard else ""

        if not url or not is_youtube_url(url):
            url, ok = QInputDialog.getText(
                self, "URL 입력", "YouTube URL을 입력하세요:",
                text=url,
            )
            if not ok or not url:
                return
            if not is_youtube_url(url):
                QMessageBox.warning(self, "오류", "올바른 YouTube URL이 아닙니다.")
                return

        self._fetch_info(url)

    def _fetch_info(self, url: str):
        if self._info_worker and self._info_worker.isRunning():
            QMessageBox.information(self, "알림", "이미 정보를 가져오는 중입니다.")
            return

        self.status_bar.showMessage("영상 정보를 가져오는 중...")
        from app.workers.info_worker import InfoWorker
        self._info_worker = InfoWorker(url)
        self._info_worker.info_ready.connect(self._on_info_ready)
        self._info_worker.playlist_ready.connect(self._on_playlist_ready)
        self._info_worker.error.connect(self._on_info_error)
        self._info_worker.status_message.connect(self.status_bar.showMessage)
        self._info_worker.start()

    def _on_info_ready(self, video_info: VideoInfo):
        video_info.download_type = self.toolbar.download_type
        video_info.selected_quality = self.toolbar.quality
        video_info.ext = self.toolbar.format

        widget = self.download_list.add_item(video_info)
        self._start_download(video_info)
        self.status_bar.showMessage("다운로드 시작...")

    def _on_playlist_ready(self, videos: list):
        self.status_bar.showMessage(f"재생목록: {len(videos)}개 영상 발견")
        for vi in videos:
            vi.download_type = self.toolbar.download_type
            vi.selected_quality = self.toolbar.quality
            vi.ext = self.toolbar.format
            self.download_list.add_item(vi)
            self._start_download(vi)

    def _on_info_error(self, msg: str):
        self.status_bar.showMessage("오류 발생")
        QMessageBox.warning(self, "오류", msg)

    # ── Download management ──────────────────────────────────

    def _start_download(self, video_info: VideoInfo):
        """Queue or start a download respecting concurrent limit."""
        max_concurrent = self._settings.concurrent_downloads
        if len(self._workers) >= max_concurrent:
            self._download_queue.append(video_info)
            widget = self.download_list.get_item(video_info.video_id)
            if widget:
                widget.lbl_status.setText("대기중")
            return

        self._launch_worker(video_info)

    def _launch_worker(self, video_info: VideoInfo):
        from app.workers.download_worker import DownloadWorker
        worker = DownloadWorker(
            video_info=video_info,
            save_dir=self.toolbar.save_path,
            download_type=self.toolbar.download_type,
            quality=self.toolbar.quality,
            fmt=self.toolbar.format,
            subtitle=self.toolbar.subtitle_enabled,
            subtitle_lang=self.toolbar.subtitle_lang,
            audio_track=self.toolbar.audio_track,
            frame_rate=self.toolbar.frame_rate,
            codec=self.toolbar.codec,
        )
        worker.progress.connect(self._on_download_progress)
        worker.finished.connect(self._on_download_finished)
        worker.error.connect(self._on_download_error)
        self._workers[video_info.video_id] = worker
        worker.start()

    def _process_queue(self):
        """Start queued downloads if slots are available."""
        max_concurrent = self._settings.concurrent_downloads
        while self._download_queue and len(self._workers) < max_concurrent:
            vi = self._download_queue.popleft()
            self._launch_worker(vi)

    def _on_download_progress(self, video_id: str, data: dict):
        widget = self.download_list.get_item(video_id)
        if widget:
            widget.update_progress(data)

    def _on_download_finished(self, video_id: str, file_path: str):
        widget = self.download_list.get_item(video_id)
        if widget:
            widget.set_completed(file_path)
            vi = widget.video_info
            self.db.add_record(
                url=vi.url,
                video_id=vi.video_id,
                title=vi.title,
                channel=vi.channel,
                thumbnail_url=vi.thumbnail_url,
                file_path=file_path,
                fmt=vi.ext,
                quality=vi.selected_quality,
                filesize=vi.filesize_approx,
                duration=vi.duration,
                download_type=vi.download_type,
            )

        self._workers.pop(video_id, None)
        self._process_queue()

        active = len(self._workers)
        queued = len(self._download_queue)
        if active > 0:
            msg = f"다운로드 중... ({active}개 진행"
            if queued > 0:
                msg += f", {queued}개 대기"
            msg += ")"
            self.status_bar.showMessage(msg)
        else:
            self.status_bar.showMessage("모든 다운로드 완료")

        # Notifications
        title = widget.video_info.title if widget else video_id
        if self._settings.notify_download_complete:
            if self._settings.notify_tray and self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    "다운로드 완료", title,
                    QSystemTrayIcon.MessageIcon.Information, 3000,
                )
            if self._settings.notify_sound:
                self._play_notification_sound()

        if widget:
            self.control_panel.update_notification(
                "다운로드 완료", widget.video_info.title
            )

        self._reapply_sort()

    def _on_download_error(self, video_id: str, msg: str):
        widget = self.download_list.get_item(video_id)
        if widget:
            widget.set_error(msg)
        self._workers.pop(video_id, None)
        self._process_queue()
        self._reapply_sort()
        self.status_bar.showMessage(f"오류: {msg}")

        # Error notification
        if self._settings.notify_download_error:
            title = widget.video_info.title if widget else video_id
            if self._settings.notify_tray and self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    "다운로드 오류", f"{title}\n{msg}",
                    QSystemTrayIcon.MessageIcon.Warning, 5000,
                )

    def _play_notification_sound(self):
        """Play system notification sound."""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def _cancel_download(self, video_id: str):
        worker = self._workers.get(video_id)
        if worker:
            worker.cancel()

    # ── Tab / Search filtering ──────────────────────────────

    def _apply_filters(self):
        """Apply both tab filter and search text filter."""
        tab_name = self.tab_bar.current_tab
        search_text = self.tab_bar.search_input.text().strip().lower()

        for item in self.download_list.get_all_items():
            # Tab filter
            if tab_name == "전체":
                tab_match = True
            elif tab_name == "동영상":
                tab_match = item.video_info.download_type == "video"
            elif tab_name == "오디오":
                tab_match = item.video_info.download_type == "audio"
            elif tab_name == "재생 목록":
                tab_match = item.video_info.is_playlist
            else:
                tab_match = True

            # Search filter
            if search_text:
                title = (item.video_info.title or "").lower()
                channel = (item.video_info.channel or "").lower()
                search_match = search_text in title or search_text in channel
            else:
                search_match = True

            item.setVisible(tab_match and search_match)

    def _on_tab_changed(self, tab_name: str):
        self._apply_filters()

    def _on_search_filter(self, text: str):
        self._apply_filters()

    def _reapply_sort(self):
        """현재 정렬 설정으로 목록을 다시 정렬한다."""
        key = self.tab_bar._sort_key
        ascending = self.tab_bar._sort_ascending
        self.download_list.sort_items(key, ascending)

    # ── Menu actions ────────────────────────────────────────

    def _change_save_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "저장 폴더 선택", self.toolbar.save_path
        )
        if path:
            self.toolbar._save_path = path
            display = self.toolbar._get_display_path()
            self.toolbar.btn_save_path.setText(f"{display}  ▾")
            self.toolbar.save_path_changed.emit(path)

    def _open_save_folder(self):
        path = self.toolbar.save_path
        if os.path.isdir(path):
            os.startfile(path)

    def _clear_list(self):
        for item in list(self.download_list.get_all_items()):
            if item.video_info.status != "downloading":
                self.download_list._remove_item(item.video_info.video_id)

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "확인", "모든 다운로드 이력을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_all()
            self._clear_list()
            self.status_bar.showMessage("이력이 삭제되었습니다")

    def _pause_all(self):
        paused = 0
        for vid, worker in self._workers.items():
            if not worker._cancelled:
                worker.cancel()
                widget = self.download_list.get_item(vid)
                if widget:
                    widget.lbl_status.setText("일시정지")
                    widget.video_info.status = "paused"
                paused += 1
        if paused > 0:
            self.status_bar.showMessage(f"{paused}개 다운로드 일시정지됨")
        else:
            self.status_bar.showMessage("일시정지할 다운로드가 없습니다")

    def _resume_all(self):
        resumed = 0
        for item in self.download_list.get_all_items():
            if item.video_info.status == "paused":
                item.video_info.status = "downloading"
                item.lbl_status.setText("대기중")
                self._start_download(item.video_info)
                resumed += 1
        if resumed > 0:
            self.status_bar.showMessage(f"{resumed}개 다운로드 재시작")
        else:
            self.status_bar.showMessage("재시작할 다운로드가 없습니다")

    def _remove_all(self):
        reply = QMessageBox.question(
            self, "확인", "모든 항목을 제거하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Cancel active downloads first
            for worker in list(self._workers.values()):
                worker.cancel()
            self._workers.clear()

            for item in list(self.download_list.get_all_items()):
                self.download_list._remove_item(item.video_info.video_id)
            self.status_bar.showMessage("모든 항목이 제거되었습니다")

    def _download_playlist_type(self, playlist_type: str):
        if playlist_type == "watch_later":
            label = "나중에 볼 동영상"
        else:
            label = "좋아요 표시한 동영상"
        QMessageBox.information(
            self, "알림",
            f'"{label}" 재생목록 다운로드는 YouTube 로그인이 필요합니다.\n'
            "현재 버전에서는 지원되지 않습니다."
        )

    def _subscribe_playlist(self, playlist_type: str):
        if playlist_type == "watch_later":
            label = "나중에 볼 동영상"
        else:
            label = "좋아요 표시한 동영상"
        QMessageBox.information(
            self, "알림",
            f'"{label}" 재생 목록 구독은 YouTube 로그인이 필요합니다.\n'
            "현재 버전에서는 지원되지 않습니다."
        )

    def _show_control_panel(self):
        self.control_panel.toggle()

    def _on_youtube_login(self):
        QMessageBox.information(
            self, "YouTube 로그인",
            "YouTube 로그인 기능은 현재 버전에서 지원되지 않습니다."
        )

    def _show_support(self):
        QMessageBox.information(
            self, "지원",
            "지원 기능은 현재 버전에서 지원되지 않습니다."
        )

    def _show_preferences(self):
        from app.widgets.preferences_dialog import PreferencesDialog
        dlg = PreferencesDialog(self)
        dlg.page_advanced.edit_path.setText(self.toolbar.save_path)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dlg.show()

    def _on_settings_changed(self):
        """React to preference changes."""
        s = self._settings

        # Sync save path from settings to toolbar
        save_path = s.default_save_path
        if save_path and save_path != self.toolbar.save_path:
            self.toolbar._save_path = save_path
            display = self.toolbar._get_display_path()
            self.toolbar.btn_save_path.setText(f"{display}  ▾")

        # Show/hide tray icon based on background setting
        if s.run_in_background:
            self.tray_icon.show()
        else:
            self.tray_icon.hide()

    def _show_license(self):
        QMessageBox.information(
            self, "라이센스",
            "라이센스 관리 기능은 현재 버전에서 지원되지 않습니다."
        )

    def _check_update(self):
        import yt_dlp
        version = getattr(yt_dlp, "version", None)
        ver_str = getattr(version, "__version__", "알 수 없음") if version else "알 수 없음"
        QMessageBox.information(
            self, "업데이트 확인",
            f"Stock Video Automator v1.0\n"
            f"yt-dlp 버전: {ver_str}\n\n"
            "도구 > yt-dlp 업데이트 메뉴에서\n"
            "yt-dlp를 최신 버전으로 업데이트할 수 있습니다."
        )

    # ── yt-dlp update ────────────────────────────────────────

    def _auto_check_ytdlp_update(self):
        """프로그램 시작 시 자동으로 yt-dlp 업데이트 체크."""
        self._run_ytdlp_update(silent=True)

    def _update_ytdlp(self):
        """사용자가 수동으로 yt-dlp 업데이트 실행."""
        if self._update_worker and self._update_worker.isRunning():
            QMessageBox.information(
                self, "알림", "이미 업데이트가 진행 중입니다."
            )
            return
        self._run_ytdlp_update(silent=False)

    def _run_ytdlp_update(self, silent: bool = False):
        import sys
        from app.workers.update_worker import YtDlpUpdateWorker
        self._update_silent = silent
        self._update_worker = YtDlpUpdateWorker(python_path=sys.executable)
        self._update_worker.status_message.connect(self._on_update_status)
        self._update_worker.finished.connect(self._on_update_finished)
        self._update_worker.start()

    def _on_update_status(self, msg: str):
        self.status_bar.showMessage(msg)

    def _on_update_finished(self, success: bool, msg: str):
        if self._update_silent:
            # 자동 체크: 상태바에만 표시
            if success:
                self.status_bar.showMessage(msg, 5000)
            else:
                self.status_bar.showMessage(f"yt-dlp 업데이트 실패: {msg}", 5000)
        else:
            # 수동 업데이트: 메시지박스로 결과 표시
            if success:
                QMessageBox.information(self, "yt-dlp 업데이트", msg)
            else:
                QMessageBox.warning(self, "yt-dlp 업데이트 실패", msg)
            self.status_bar.showMessage("준비")

    def _show_about(self):
        QMessageBox.about(
            self, "Stock Video Automator",
            "Stock Video Automator v1.0\n\n"
            "PyQt6 + yt-dlp 기반 비디오 다운로더\n"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        central = self.centralWidget()
        if central and hasattr(self, 'control_panel'):
            self.control_panel.reposition(
                central.width(), central.height()
            )

    def closeEvent(self, event):
        # Minimize to tray if background running is enabled
        if self._settings.run_in_background and not self._force_quit:
            event.ignore()
            self.hide()
            if self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    "Stock Video Automator",
                    "백그라운드에서 실행 중입니다.",
                    QSystemTrayIcon.MessageIcon.Information, 2000,
                )
            return

        # Actually quit: stop bridge server and cancel all running downloads
        if hasattr(self, '_bridge_server'):
            self._bridge_server.stop()
        for worker in self._workers.values():
            worker.cancel()
            worker.wait(2000)
        self.tray_icon.hide()
        event.accept()
