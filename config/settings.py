"""
全局配置系统 - 管理所有应用级别的设置
"""
import os
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict


APP_NAME = "抖音切片剪辑工具"
APP_VERSION = "1.0.0"
IS_WINDOWS = sys.platform == "win32"
FFMPEG_EXE = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"
FFPROBE_EXE = "ffprobe.exe" if IS_WINDOWS else "ffprobe"


def _get_bundle_dir() -> Path:
    """获取PyInstaller打包后的资源目录"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


def _find_ffmpeg(name: str) -> str:
    """在多个可能位置查找FFmpeg二进制"""
    search_paths = []

    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
        # PyInstaller --add-binary 解压后的路径
        search_paths += [
            base / "bin" / name,
            base / name,
        ]

    # 可执行文件同目录（用户手动放入）
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        search_paths.append(exe_dir / name)

    # 开发模式下的常见路径
    search_paths.append(Path(__file__).parent.parent / "bin" / name)

    for p in search_paths:
        if p.exists():
            return str(p)

    # fallback: 系统PATH
    return name


def get_ffmpeg_path() -> str:
    """获取FFmpeg二进制路径"""
    return _find_ffmpeg(FFMPEG_EXE)


def get_ffprobe_path() -> str:
    """获取ffprobe二进制路径"""
    return _find_ffmpeg(FFPROBE_EXE)


# 基础路径
BASE_DIR = Path.home() / "Documents" / "DouyinClipTool"
CONFIG_DIR = BASE_DIR / "config"
MODELS_DIR = BASE_DIR / "models"
CACHE_DIR = BASE_DIR / "cache"
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

# 自动创建目录
for d in [CONFIG_DIR, MODELS_DIR, CACHE_DIR, TEMP_DIR, OUTPUT_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class VideoSettings:
    """视频处理默认参数"""
    resolution_width: int = 1080
    resolution_height: int = 1920
    fps: int = 30
    bitrate: str = "10M"
    codec: str = "h264"
    pixel_format: str = "yuv420p"
    aspect_ratio: str = "9:16"


@dataclass
class AudioSettings:
    """音频处理默认参数"""
    sample_rate: int = 44100
    bitrate: str = "192k"
    codec: str = "aac"
    channels: int = 2
    volume_db: float = 0.0


@dataclass
class ExportSettings:
    """导出默认参数"""
    format: str = "mp4"
    video: VideoSettings = field(default_factory=VideoSettings)
    audio: AudioSettings = field(default_factory=AudioSettings)
    output_dir: str = field(default_factory=lambda: str(OUTPUT_DIR))
    hardware_accel: bool = True


@dataclass
class DedupSettings:
    """去重默认参数"""
    intensity: str = "中"  # 低 / 中 / 高
    mirror: bool = False
    speed_change: float = 0.0
    crop_percent: float = 0.02
    scale_range: tuple = (0.98, 1.02)
    rotation_range: tuple = (-1.5, 1.5)
    brightness_range: tuple = (-0.05, 0.05)
    contrast_range: tuple = (-0.08, 0.08)
    saturation_range: tuple = (-0.03, 0.05)
    frame_offset: int = 2
    drop_frames: int = 1
    border_enabled: bool = False
    watermark_enabled: bool = False
    watermark_text: str = ""
    filter_enabled: bool = False
    shake_enabled: bool = False


@dataclass
class AISettings:
    """AI引擎参数"""
    ollama_host: str = "http://localhost:11434"
    vision_model: str = "qwen2.5-vl:7b"
    strategy_model: str = "qwen2.5:7b"
    whisper_model: str = "large-v3"
    use_gpu: bool = True
    analysis_frame_interval: int = 30  # 每30帧采样一帧用于AI分析
    max_analysis_frames: int = 15      # 单次最多分析15帧


@dataclass
class AppConfig:
    """应用总配置"""
    video: VideoSettings = field(default_factory=VideoSettings)
    audio: AudioSettings = field(default_factory=AudioSettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    dedup: DedupSettings = field(default_factory=DedupSettings)
    ai: AISettings = field(default_factory=AISettings)
    language: str = "zh_CN"
    max_recent_projects: int = 5
    auto_save_interval: int = 300

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: str = None):
        path = path or str(CONFIG_DIR / "app_config.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str = None) -> "AppConfig":
        path = path or str(CONFIG_DIR / "app_config.json")
        if not os.path.exists(path):
            config = cls()
            config.save(path)
            return config
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


# 全局配置单例
app_config = AppConfig.load()

# 日志实例（统一从settings导出，避免多处import utils.logger）
from utils.logger import log
