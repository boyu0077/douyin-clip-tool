"""
片段数据模型 - 时间轴上的单个片段
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import uuid


@dataclass
class Clip:
    """视频片段"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    source_path: str = ""
    
    # 时间轴位置
    timeline_start: float = 0.0  # 在时间轴上的起始位置(秒)
    timeline_end: float = 0.0    # 在时间轴上的结束位置(秒)
    
    # 源文件裁剪
    source_start: float = 0.0    # 源文件入点(秒)
    source_end: float = 0.0      # 源文件出点(秒)
    
    # 变换属性
    speed: float = 1.0           # 播放速度 (1.0 = 原速)
    volume: float = 1.0          # 音量
    opacity: float = 1.0         # 透明度
    
    # 效果标记（非渲染用，渲染用Effector）
    mirror: bool = False
    rotation: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    
    # 轨道ID
    track_id: str = "video_0"
    
    # 缩略图缓存
    thumbnail_path: Optional[str] = None
    
    @property
    def duration(self) -> float:
        return self.timeline_end - self.timeline_start
    
    @property
    def source_duration(self) -> float:
        return self.source_end - self.source_start
    
    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "source_path": self.source_path,
            "timeline_start": self.timeline_start, "timeline_end": self.timeline_end,
            "source_start": self.source_start, "source_end": self.source_end,
            "speed": self.speed, "volume": self.volume, "opacity": self.opacity,
            "mirror": self.mirror, "rotation": self.rotation,
            "scale_x": self.scale_x, "scale_y": self.scale_y,
            "track_id": self.track_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Clip":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SubtitleItem:
    """字幕条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    text: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    color: str = "#FFFFFF"
    font_size: int = 48
    position: str = "bottom"  # bottom | middle | top
    animation: str = "none"   # none | fade_in | typewriter | slide_up
    
    def to_dict(self) -> dict:
        return {
            "id": self.id, "text": self.text,
            "start_time": self.start_time, "end_time": self.end_time,
            "color": self.color, "font_size": self.font_size,
            "position": self.position, "animation": self.animation,
        }
