"""视频信息读取 - 通过ffprobe获取视频元数据"""
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from config.settings import log, get_ffprobe_path


@dataclass
class VideoInfo:
    """视频文件完整信息"""
    filepath: str
    filename: str
    width: int = 0
    height: int = 0
    fps: float = 0.0
    duration: float = 0.0
    video_codec: str = ""
    audio_codec: str = ""
    video_bitrate: int = 0
    audio_bitrate: int = 0
    sample_rate: int = 0
    audio_channels: int = 0
    total_frames: int = 0
    file_size_mb: float = 0.0

    @property
    def aspect_ratio(self) -> str:
        if self.width > self.height:
            return f"{self.width}:{self.height} (横屏)"
        return f"{self.width}:{self.height} (竖屏)"

    @property
    def is_portrait(self) -> bool:
        return self.height > self.width

    @property
    def duration_str(self) -> str:
        m, s = divmod(int(self.duration), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"


def parse_ffprobe_output(output: str, filepath: str) -> VideoInfo:
    """解析 ffprobe JSON 输出"""
    data = json.loads(output)
    info = VideoInfo(
        filepath=str(filepath),
        filename=Path(filepath).name,
    )
    try:
        info.file_size_mb = Path(filepath).stat().st_size / (1024 * 1024)
    except Exception:
        pass

    for stream in data.get("streams", []):
        codec_type = stream.get("codec_type", "")
        if codec_type == "video":
            info.width = stream.get("width", 0)
            info.height = stream.get("height", 0)
            fps_str = stream.get("r_frame_rate", "0/1")
            num, den = fps_str.split("/")
            info.fps = round(int(num) / int(den), 2) if int(den) else 0
            info.video_codec = stream.get("codec_name", "")
            info.video_bitrate = int(stream.get("bit_rate", 0) or 0)
            info.total_frames = int(stream.get("nb_frames", 0) or 0)
        elif codec_type == "audio":
            info.audio_codec = stream.get("codec_name", "")
            info.audio_bitrate = int(stream.get("bit_rate", 0) or 0)
            info.sample_rate = int(stream.get("sample_rate", 0) or 0)
            info.audio_channels = stream.get("channels", 0)

    fmt = data.get("format", {})
    info.duration = float(fmt.get("duration", 0))
    if info.total_frames == 0 and info.fps > 0:
        info.total_frames = int(info.duration * info.fps)

    return info


def get_video_info(filepath: str) -> Optional[VideoInfo]:
    """获取视频文件完整信息"""
    try:
        cmd = [
            get_ffprobe_path(), "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            log.error(f"ffprobe失败: {result.stderr}")
            return None
        return parse_ffprobe_output(result.stdout, filepath)
    except FileNotFoundError:
        log.error("ffprobe未找到，请安装FFmpeg")
        return None
    except Exception as e:
        log.error(f"读取视频信息失败: {e}")
        return None
