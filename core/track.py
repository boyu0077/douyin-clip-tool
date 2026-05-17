"""
轨道数据模型
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from core.clip import Clip


class TrackType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    OVERLAY = "overlay"


@dataclass
class Track:
    """时间轴轨道"""
    id: str
    name: str
    track_type: str = "video"  # video | audio | subtitle | overlay
    clips: list[Clip] = field(default_factory=list)
    muted: bool = False
    locked: bool = False
    solo: bool = False
    height: int = 80
    
    def add_clip(self, clip: Clip):
        self.clips.append(clip)
        self.clips.sort(key=lambda c: c.timeline_start)
    
    def remove_clip(self, clip_id: str):
        self.clips = [c for c in self.clips if c.id != clip_id]
    
    def clip_at(self, time: float) -> Optional[Clip]:
        for clip in self.clips:
            if clip.timeline_start <= time < clip.timeline_end:
                return clip
        return None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "track_type": self.track_type,
            "clips": [c.to_dict() for c in self.clips],
            "muted": self.muted, "locked": self.locked, "solo": self.solo,
        }


@dataclass
class TrackGroup:
    """轨道组"""
    video_tracks: list[Track] = field(default_factory=list)
    audio_tracks: list[Track] = field(default_factory=list)
    subtitle_tracks: list[Track] = field(default_factory=list)
    overlay_tracks: list[Track] = field(default_factory=list)
    
    def all_tracks(self) -> list[Track]:
        return self.video_tracks + self.audio_tracks + self.subtitle_tracks + self.overlay_tracks
