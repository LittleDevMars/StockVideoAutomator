# Stock Video Automator

PyQt6 + yt-dlp 기반 YouTube 비디오/오디오 다운로더.

## MCP 서버 (Claude Code 연동)

앱이 실행 중일 때 Claude Code에서 MCP 도구로 앱을 제어할 수 있습니다.

### 사전 조건
- 앱이 실행 중이어야 합니다 (`run.bat` 또는 `python main.py`)
- TCP 포트 19384에서 bridge server가 대기

### 사용 가능한 MCP 도구

| 도구 | 설명 | 예시 |
|------|------|------|
| `add_download` | URL로 다운로드 추가 | `add_download(url="https://youtu.be/xxxxx")` |
| `get_downloads` | 현재 다운로드 목록 조회 | `get_downloads()` |
| `get_download_status` | 특정 다운로드 상태 조회 | `get_download_status(video_id="xxxxx")` |
| `cancel_download` | 다운로드 취소 | `cancel_download(video_id="xxxxx")` |
| `get_settings` | 현재 설정 조회 | `get_settings()` |
| `update_settings` | 설정 변경 | `update_settings(format="MKV", quality="1080p")` |
| `get_history` | 다운로드 이력 조회 | `get_history()` |
| `pause_all` | 모든 다운로드 일시정지 | `pause_all()` |
| `resume_all` | 모든 다운로드 재개 | `resume_all()` |

### update_settings 파라미터

- `download_type`: "video" | "audio"
- `format`: "MP4" | "MKV" | "WEBM" | "MP3" | "M4A" | "WAV" | "FLAC"
- `quality`: "best" | "1080p" | "720p" | "480p" | "360p"
- `codec`: "H264" | "H265" | "VP9" | "AV1"
- `frame_rate`: "최고" | "60fps" | "30fps" | "24fps"
- `subtitle_enabled`: true | false
- `subtitle_lang`: "한국어" | "English" | "日本語" | "中文"
- `audio_track`: "기본" | "모든 트랙"

## 프로젝트 구조

- `app/main_window.py` — 메인 윈도우 (다운로드 관리)
- `app/widgets/` — UI 위젯 (toolbar, tab_bar, download_list 등)
- `app/workers/` — 백그라운드 워커 (download, info, update)
- `app/models/` — 데이터 모델 (VideoInfo, Database)
- `app/utils/` — 유틸리티 (settings, helpers, dependency_installer)
- `app/bridge/` — TCP bridge server (MCP 연동)
- `app/mcp/` — MCP 서버 (Claude Code용)

## 빌드

```bash
# Windows
python -m PyInstaller StockVideoAutomator.spec --clean -y

# macOS
python3 -m PyInstaller StockVideoAutomator-mac.spec --clean -y
```
