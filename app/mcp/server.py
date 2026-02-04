"""MCP server for Claude Code to control the YouTube Downloader app.

Run with: python -m app.mcp.server
Uses stdio transport for communication with Claude Code.
"""

from mcp.server.fastmcp import FastMCP

from app.mcp.bridge_client import BridgeClient

mcp = FastMCP("youtube-downloader")
bridge = BridgeClient()


@mcp.tool()
def add_download(url: str) -> str:
    """Add a YouTube video/audio download by URL.

    Args:
        url: YouTube video or playlist URL to download
    """
    result = bridge.send_request("add_download", {"url": url})
    return f"Download started for: {url} (status: {result.get('status', 'unknown')})"


@mcp.tool()
def get_downloads() -> list[dict]:
    """Get list of all current downloads with their status.

    Returns a list of download items with video_id, title, status, progress, etc.
    """
    return bridge.send_request("get_downloads")


@mcp.tool()
def get_download_status(video_id: str) -> dict:
    """Get detailed status of a specific download.

    Args:
        video_id: The YouTube video ID to check status for
    """
    return bridge.send_request("get_download_status", {"video_id": video_id})


@mcp.tool()
def cancel_download(video_id: str) -> str:
    """Cancel an active download.

    Args:
        video_id: The YouTube video ID to cancel
    """
    result = bridge.send_request("cancel_download", {"video_id": video_id})
    return f"Cancel requested for: {video_id}"


@mcp.tool()
def get_settings() -> dict:
    """Get current download settings.

    Returns download_type, format, quality, codec, frame_rate,
    subtitle_enabled, subtitle_lang, audio_track, save_path.
    """
    return bridge.send_request("get_settings")


@mcp.tool()
def update_settings(
    download_type: str | None = None,
    format: str | None = None,
    quality: str | None = None,
    codec: str | None = None,
    frame_rate: str | None = None,
    subtitle_enabled: bool | None = None,
    subtitle_lang: str | None = None,
    audio_track: str | None = None,
) -> dict:
    """Update download settings.

    Args:
        download_type: "video" or "audio"
        format: Video format - "MP4", "MKV", "WEBM" / Audio format - "MP3", "M4A", "WAV", "FLAC"
        quality: Video quality - "best", "1080p", "720p", "480p", "360p"
        codec: Video codec - "H264", "H265", "VP9", "AV1"
        frame_rate: Frame rate - "최고", "60fps", "30fps", "24fps"
        subtitle_enabled: Enable/disable subtitle download
        subtitle_lang: Subtitle language - "한국어", "English", "日本語", "中文"
        audio_track: Audio track - "기본" (default) or "모든 트랙" (all tracks)
    """
    params = {}
    if download_type is not None:
        params["download_type"] = download_type
    if format is not None:
        params["format"] = format
    if quality is not None:
        params["quality"] = quality
    if codec is not None:
        params["codec"] = codec
    if frame_rate is not None:
        params["frame_rate"] = frame_rate
    if subtitle_enabled is not None:
        params["subtitle_enabled"] = subtitle_enabled
    if subtitle_lang is not None:
        params["subtitle_lang"] = subtitle_lang
    if audio_track is not None:
        params["audio_track"] = audio_track

    return bridge.send_request("update_settings", params)


@mcp.tool()
def get_history() -> list[dict]:
    """Get download history.

    Returns list of previously completed downloads with video_id, title,
    channel, url, file_path, format, quality, filesize, duration.
    """
    return bridge.send_request("get_history")


@mcp.tool()
def pause_all() -> str:
    """Pause all active downloads."""
    bridge.send_request("pause_all")
    return "All downloads paused"


@mcp.tool()
def resume_all() -> str:
    """Resume all paused downloads."""
    bridge.send_request("resume_all")
    return "All downloads resumed"


if __name__ == "__main__":
    mcp.run()
