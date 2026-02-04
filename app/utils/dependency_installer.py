"""Auto-download ffmpeg and deno if not found on the system."""

import os
import io
import sys
import shutil
import platform
import zipfile
import tarfile
import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal


def get_tools_dir() -> str:
    """Return the tools directory next to the executable or project root."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tools = os.path.join(base, "tools")
    os.makedirs(tools, exist_ok=True)
    return tools


def find_ffmpeg() -> str | None:
    """Find ffmpeg on PATH or known locations."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    tools = get_tools_dir()
    ext = ".exe" if sys.platform == "win32" else ""
    local = os.path.join(tools, f"ffmpeg{ext}")
    if os.path.isfile(local):
        return local
    return None


def find_deno() -> str | None:
    """Find deno on PATH or known locations."""
    found = shutil.which("deno")
    if found:
        return found
    # Check ~/.deno/bin
    deno_bin = os.path.join(os.path.expanduser("~"), ".deno", "bin")
    ext = ".exe" if sys.platform == "win32" else ""
    deno_path = os.path.join(deno_bin, f"deno{ext}")
    if os.path.isfile(deno_path):
        return deno_path
    # Check tools dir
    tools = get_tools_dir()
    local = os.path.join(tools, f"deno{ext}")
    if os.path.isfile(local):
        return local
    return None


def add_tools_to_path():
    """Add tools directory to PATH if it exists."""
    tools = get_tools_dir()
    if os.path.isdir(tools) and tools not in os.environ.get("PATH", ""):
        os.environ["PATH"] = tools + os.pathsep + os.environ.get("PATH", "")
    # Also add ~/.deno/bin
    deno_bin = os.path.join(os.path.expanduser("~"), ".deno", "bin")
    if os.path.isdir(deno_bin) and deno_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = deno_bin + os.pathsep + os.environ.get("PATH", "")


# ── Download URLs ─────────────────────────────────────────

def _ffmpeg_url() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Windows":
        return "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    elif system == "Darwin":
        if "arm" in machine or "aarch64" in machine:
            return "https://evermeet.cx/ffmpeg/getrelease/zip"
        return "https://evermeet.cx/ffmpeg/getrelease/zip"
    else:  # Linux
        return "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"


def _deno_url() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Windows":
        return "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip"
    elif system == "Darwin":
        if "arm" in machine or "aarch64" in machine:
            return "https://github.com/denoland/deno/releases/latest/download/deno-aarch64-apple-darwin.zip"
        return "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-apple-darwin.zip"
    else:  # Linux
        return "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip"


# ── Installer thread ─────────────────────────────────────

class DependencyInstaller(QThread):
    """Background thread to download missing dependencies."""

    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, install_ffmpeg=True, install_deno=True, parent=None):
        super().__init__(parent)
        self._install_ffmpeg = install_ffmpeg
        self._install_deno = install_deno

    def run(self):
        tools = get_tools_dir()
        errors = []

        if self._install_ffmpeg:
            try:
                self.status.emit("ffmpeg 다운로드 중...")
                self._download_ffmpeg(tools)
                self.status.emit("ffmpeg 설치 완료")
            except Exception as e:
                errors.append(f"ffmpeg: {e}")

        if self._install_deno:
            try:
                self.status.emit("deno 다운로드 중...")
                self._download_deno(tools)
                self.status.emit("deno 설치 완료")
            except Exception as e:
                errors.append(f"deno: {e}")

        add_tools_to_path()

        if errors:
            self.finished.emit(False, "\n".join(errors))
        else:
            self.finished.emit(True, "모든 의존성 설치 완료")

    def _download_ffmpeg(self, tools_dir: str):
        url = _ffmpeg_url()
        data = self._download(url)
        ext = ".exe" if sys.platform == "win32" else ""

        if url.endswith(".tar.xz"):
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as tar:
                for member in tar.getmembers():
                    basename = os.path.basename(member.name)
                    if basename in ("ffmpeg", "ffprobe", "ffmpeg.exe", "ffprobe.exe"):
                        member.name = basename
                        tar.extract(member, tools_dir)
        else:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for name in zf.namelist():
                    basename = os.path.basename(name)
                    if basename in (f"ffmpeg{ext}", f"ffprobe{ext}"):
                        target = os.path.join(tools_dir, basename)
                        with zf.open(name) as src, open(target, "wb") as dst:
                            dst.write(src.read())
                        if sys.platform != "win32":
                            os.chmod(target, 0o755)

    def _download_deno(self, tools_dir: str):
        url = _deno_url()
        data = self._download(url)
        ext = ".exe" if sys.platform == "win32" else ""

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                basename = os.path.basename(name)
                if basename in (f"deno{ext}", f"deno"):
                    target = os.path.join(tools_dir, f"deno{ext}")
                    with zf.open(name) as src, open(target, "wb") as dst:
                        dst.write(src.read())
                    if sys.platform != "win32":
                        os.chmod(target, 0o755)

    def _download(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "StockVideoAutomator/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
