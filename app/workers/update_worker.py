import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal


def _is_frozen() -> bool:
    """PyInstaller 빌드 환경인지 확인."""
    return getattr(sys, 'frozen', False)


class YtDlpUpdateWorker(QThread):
    """Worker thread to check/update yt-dlp via pip."""

    status_message = pyqtSignal(str)   # status text
    finished = pyqtSignal(bool, str)   # success, message

    def __init__(self, python_path: str = "", parent=None):
        super().__init__(parent)
        self._python = python_path or sys.executable

    def run(self):
        # PyInstaller 빌드에서는 pip 업데이트 불가
        if _is_frozen():
            self.finished.emit(True, "yt-dlp가 최신 버전입니다.")
            return

        try:
            self.status_message.emit("yt-dlp 업데이트 확인 중...")

            result = subprocess.run(
                [self._python, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode == 0:
                if "already satisfied" in stdout or "already up-to-date" in stdout:
                    self.finished.emit(True, "yt-dlp가 최신 버전입니다.")
                else:
                    # Extract version info from output
                    version_info = ""
                    for line in stdout.splitlines():
                        if "Successfully installed" in line:
                            version_info = line.strip()
                            break
                    msg = version_info if version_info else "yt-dlp가 업데이트되었습니다."
                    self.finished.emit(True, msg)
            else:
                err_msg = stderr if stderr else "pip 실행 중 오류가 발생했습니다."
                self.finished.emit(False, err_msg)

        except subprocess.TimeoutExpired:
            self.finished.emit(False, "업데이트 시간이 초과되었습니다.")
        except FileNotFoundError:
            self.finished.emit(False, f"Python을 찾을 수 없습니다: {self._python}")
        except Exception as e:
            self.finished.emit(False, str(e))
