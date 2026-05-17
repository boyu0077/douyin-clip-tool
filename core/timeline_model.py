"""
时间轴数据模型 - 管理所有轨道和片段
"""
from dataclasses import dataclass, field
from core.track import Track, TrackGroup
from core.clip import Clip, SubtitleItem


@dataclass
class TimelineModel:
    """时间轴数据模型"""
    duration: float = 0.0
    fps: int = 30
    resolution: tuple = (1080, 1920)
    
    tracks: TrackGroup = field(default_factory=TrackGroup)
    subtitles: list[SubtitleItem] = field(default_factory=list)
    markers: list[float] = field(default_factory=list)  # 标记点(秒)
    
    def __post_init__(self):
        # 默认创建4条轨道
        if not self.tracks.video_tracks:
            self.tracks.video_tracks.append(Track(id="video_0", name="视频轨", track_type="video"))
        if not self.tracks.audio_tracks:
            self.tracks.audio_tracks.append(Track(id="audio_0", name="音频轨", track_type="audio"))
        if not self.tracks.subtitle_tracks:
            self.tracks.subtitle_tracks.append(Track(id="subtitle_0", name="字幕轨", track_type="subtitle"))
        if not self.tracks.overlay_tracks:
            self.tracks.overlay_tracks.append(Track(id="overlay_0", name="叠加轨", track_type="overlay"))
    
    def add_clip(self, clip: Clip, track_type: str = "video", track_id: str = ""):
        track = self._find_or_create_track(track_type, track_id)
        track.add_clip(clip)
        self._update_duration()
    
    def remove_clip(self, clip_id: str):
        for track in self.tracks.all_tracks():
            track.remove_clip(clip_id)
        self._update_duration()
    
    def clip_at(self, time: float) -> Clip | None:
        for track in self.tracks.video_tracks:
            c = track.clip_at(time)
            if c: return c
        return None
    
    def get_clip(self, clip_id: str) -> Clip | None:
        for track in self.tracks.all_tracks():
            for c in track.clips:
                if c.id == clip_id:
                    return c
        return None
    
    def _find_or_create_track(self, track_type: str, track_id: str) -> Track:
        track_list = {
            "video": self.tracks.video_tracks,
            "audio": self.tracks.audio_tracks,
            "subtitle": self.tracks.subtitle_tracks,
            "overlay": self.tracks.overlay_tracks,
        }.get(track_type, self.tracks.video_tracks)
        
        if track_id:
            for t in track_list:
                if t.id == track_id:
                    return t
        
        new_track = Track(
            id=track_id or f"{track_type}_{len(track_list)}",
            name=f"{track_type}轨 {len(track_list)+1}",
            track_type=track_type
        )
        track_list.append(new_track)
        return new_track
    
    def _update_duration(self):
        max_end = 0.0
        for track in self.tracks.all_tracks():
            for clip in track.clips:
                if clip.timeline_end > max_end:
                    max_end = clip.timeline_end
        self.duration = max_end
    
    def to_dict(self) -> dict:
        return {
            "duration": self.duration, "fps": self.fps,
            "resolution": list(self.resolution),
            "tracks": {
                "video": [t.to_dict() for t in self.tracks.video_tracks],
                "audio": [t.to_dict() for t in self.tracks.audio_tracks],
                "subtitle": [t.to_dict() for t in self.tracks.subtitle_tracks],
                "overlay": [t.to_dict() for t in self.tracks.overlay_tracks],
            },
            "subtitles": [s.to_dict() for s in self.subtitles],
            "markers": self.markers,
        }
