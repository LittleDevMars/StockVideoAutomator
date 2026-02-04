"""TCP bridge server running inside the Qt application.

Listens on localhost:19384 for JSON-RPC 2.0 requests from the MCP server
process and dispatches them to MainWindow methods on the main thread.
"""

import json
import traceback
from typing import Any, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QMetaObject, Qt, Q_ARG
from PyQt6.QtNetwork import QTcpServer, QTcpSocket, QHostAddress


BRIDGE_PORT = 19384


class BridgeServer(QObject):
    """QTcpServer-based JSON-RPC bridge inside the Qt app."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self._server = QTcpServer(self)
        self._clients: list[QTcpSocket] = []
        self._buffers: dict[QTcpSocket, bytes] = {}

    def start(self) -> bool:
        ok = self._server.listen(QHostAddress.SpecialAddress.LocalHost, BRIDGE_PORT)
        if ok:
            self._server.newConnection.connect(self._on_new_connection)
            print(f"[BridgeServer] Listening on localhost:{BRIDGE_PORT}")
        else:
            print(f"[BridgeServer] Failed to listen: {self._server.errorString()}")
        return ok

    def stop(self):
        for client in self._clients:
            client.disconnectFromHost()
        self._clients.clear()
        self._buffers.clear()
        self._server.close()

    def _on_new_connection(self):
        while self._server.hasPendingConnections():
            sock = self._server.nextPendingConnection()
            self._clients.append(sock)
            self._buffers[sock] = b""
            sock.readyRead.connect(lambda s=sock: self._on_data_ready(s))
            sock.disconnected.connect(lambda s=sock: self._on_disconnected(s))

    def _on_disconnected(self, sock: QTcpSocket):
        if sock in self._clients:
            self._clients.remove(sock)
        self._buffers.pop(sock, None)
        sock.deleteLater()

    def _on_data_ready(self, sock: QTcpSocket):
        self._buffers[sock] = self._buffers.get(sock, b"") + bytes(sock.readAll())
        while b"\n" in self._buffers[sock]:
            line, rest = self._buffers[sock].split(b"\n", 1)
            self._buffers[sock] = rest
            self._process_line(sock, line)

    def _process_line(self, sock: QTcpSocket, line: bytes):
        try:
            req = json.loads(line.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_error(sock, None, -32700, f"Parse error: {e}")
            return

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        try:
            result = self._dispatch(method, params)
            self._send_result(sock, req_id, result)
        except Exception as e:
            self._send_error(sock, req_id, -1, str(e))

    def _send_result(self, sock: QTcpSocket, req_id, result):
        resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
        self._write(sock, resp)

    def _send_error(self, sock: QTcpSocket, req_id, code: int, message: str):
        resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
        self._write(sock, resp)

    def _write(self, sock: QTcpSocket, data: dict):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8") + b"\n"
        sock.write(payload)
        sock.flush()

    # ── Request dispatch ──────────────────────────────────────

    def _dispatch(self, method: str, params: dict) -> Any:
        handler = {
            "add_download": self._handle_add_download,
            "get_downloads": self._handle_get_downloads,
            "get_download_status": self._handle_get_download_status,
            "cancel_download": self._handle_cancel_download,
            "get_settings": self._handle_get_settings,
            "update_settings": self._handle_update_settings,
            "get_history": self._handle_get_history,
            "pause_all": self._handle_pause_all,
            "resume_all": self._handle_resume_all,
        }.get(method)

        if handler is None:
            raise ValueError(f"Unknown method: {method}")
        return handler(params)

    def _handle_add_download(self, params: dict) -> dict:
        url = params.get("url", "")
        if not url:
            raise ValueError("url is required")

        mw = self._main_window
        mw._fetch_info(url)
        return {"status": "info_fetch_started", "url": url}

    def _handle_get_downloads(self, params: dict) -> list:
        items = self._main_window.download_list.get_all_items()
        return [self._widget_to_dict(w) for w in items]

    def _handle_get_download_status(self, params: dict) -> dict:
        video_id = params.get("video_id", "")
        if not video_id:
            raise ValueError("video_id is required")
        widget = self._main_window.download_list.get_item(video_id)
        if widget is None:
            raise ValueError(f"Download not found: {video_id}")
        return self._widget_to_dict(widget)

    def _handle_cancel_download(self, params: dict) -> dict:
        video_id = params.get("video_id", "")
        if not video_id:
            raise ValueError("video_id is required")
        self._main_window._cancel_download(video_id)
        return {"status": "cancel_requested", "video_id": video_id}

    def _handle_get_settings(self, params: dict) -> dict:
        tb = self._main_window.toolbar
        return {
            "download_type": tb.download_type,
            "format": tb.format,
            "quality": tb.quality,
            "codec": tb.codec,
            "frame_rate": tb.frame_rate,
            "subtitle_enabled": tb.subtitle_enabled,
            "subtitle_lang": tb.subtitle_lang,
            "audio_track": tb.audio_track,
            "save_path": tb.save_path,
        }

    def _handle_update_settings(self, params: dict) -> dict:
        tb = self._main_window.toolbar
        updated = []

        if "download_type" in params:
            tb._set_download_type(params["download_type"])
            updated.append("download_type")
        if "format" in params:
            tb._set_format(params["format"])
            updated.append("format")
        if "quality" in params:
            val = params["quality"]
            tb._set_quality(val, val)
            updated.append("quality")
        if "codec" in params:
            tb._set_codec(params["codec"])
            updated.append("codec")
        if "frame_rate" in params:
            tb._set_frame_rate(params["frame_rate"])
            updated.append("frame_rate")
        if "subtitle_enabled" in params or "subtitle_lang" in params:
            enabled = params.get("subtitle_enabled", tb.subtitle_enabled)
            lang = params.get("subtitle_lang", tb.subtitle_lang)
            tb._set_subtitle(enabled, lang)
            if "subtitle_enabled" in params:
                updated.append("subtitle_enabled")
            if "subtitle_lang" in params:
                updated.append("subtitle_lang")
        if "audio_track" in params:
            tb._set_audio_track(params["audio_track"])
            updated.append("audio_track")

        return {"updated": updated}

    def _handle_get_history(self, params: dict) -> list:
        records = self._main_window.db.get_all_records()
        return [
            {
                "video_id": r.get("video_id", ""),
                "title": r.get("title", ""),
                "channel": r.get("channel", ""),
                "url": r.get("url", ""),
                "file_path": r.get("file_path", ""),
                "format": r.get("format", ""),
                "quality": r.get("quality", ""),
                "filesize": r.get("filesize", 0),
                "duration": r.get("duration", 0),
                "download_type": r.get("download_type", "video"),
            }
            for r in records
        ]

    def _handle_pause_all(self, params: dict) -> dict:
        self._main_window._pause_all()
        return {"status": "paused"}

    def _handle_resume_all(self, params: dict) -> dict:
        self._main_window._resume_all()
        return {"status": "resumed"}

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _widget_to_dict(widget) -> dict:
        vi = widget.video_info
        return {
            "video_id": vi.video_id,
            "title": vi.title,
            "channel": vi.channel,
            "url": vi.url,
            "status": vi.status,
            "progress": vi.progress,
            "speed": vi.speed,
            "eta": vi.eta,
            "filesize_approx": vi.filesize_approx,
            "download_type": vi.download_type,
            "format": vi.ext,
            "quality": vi.selected_quality,
            "downloaded_path": vi.downloaded_path,
            "error_message": vi.error_message,
        }
