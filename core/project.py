"""
项目文件管理 - 保存/加载完整工程
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from core.timeline_model import TimelineModel


@dataclass
class Project:
    """完整项目"""
    name: str = "未命名项目"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    project_path: str = ""
    
    timeline: TimelineModel = field(default_factory=TimelineModel)
    
    # 去重配置
    dedup_preset: str = "中"       # 使用的去重模板名
    dedup_intensity: str = "medium"  # light | medium | strong
    
    # 导出配置
    export_preset: str = "抖音竖屏1080P"
    
    # 元数据
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    
    def save(self, path: str = ""):
        """保存项目文件"""
        path = path or self.project_path
        if not path:
            path = str(Path.home() / "Documents" / "DouyinClipTool" / f"{self.name}.dct")
        self.project_path = path
        self.modified_at = datetime.now().isoformat()
        
        data = {
            "version": "1.0.0",
            "name": self.name,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "timeline": self.timeline.to_dict(),
            "dedup_preset": self.dedup_preset,
            "dedup_intensity": self.dedup_intensity,
            "export_preset": self.export_preset,
            "notes": self.notes,
            "tags": self.tags,
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "Project":
        """加载项目文件"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        project = cls(
            name=data["name"],
            created_at=data.get("created_at", ""),
            project_path=path,
            dedup_preset=data.get("dedup_preset", "中"),
            dedup_intensity=data.get("dedup_intensity", "medium"),
            export_preset=data.get("export_preset", "抖音竖屏1080P"),
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
        )
        
        # 恢复时间轴
        if "timeline" in data:
            from core.clip import Clip, SubtitleItem
            tdata = data["timeline"]
            project.timeline = TimelineModel(
                duration=tdata.get("duration", 0),
                fps=tdata.get("fps", 30),
                resolution=tuple(tdata.get("resolution", [1080, 1920])),
            )
            project.timeline.markers = tdata.get("markers", [])
            
            # 恢复字幕
            for sdata in tdata.get("subtitles", []):
                project.timeline.subtitles.append(SubtitleItem(**sdata))
            
            # 恢复片段到轨道
            for track_type, tracks_data in tdata.get("tracks", {}).items():
                track_list = getattr(project.timeline.tracks, {
                    "video": "video_tracks",
                    "audio": "audio_tracks",
                    "subtitle": "subtitle_tracks",
                    "overlay": "overlay_tracks",
                }.get(track_type, "video_tracks"))
                
                for tdata_item in tracks_data:
                    from core.track import Track
                    track = Track(
                        id=tdata_item["id"],
                        name=tdata_item["name"],
                        track_type=tdata_item.get("track_type", track_type),
                        muted=tdata_item.get("muted", False),
                        locked=tdata_item.get("locked", False),
                    )
                    for cdata in tdata_item.get("clips", []):
                        track.clips.append(Clip.from_dict(cdata))
                    track_list.append(track)
        
        return project
