"""字幕编辑器 - 手动编辑 + 导入导出SRT"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SubtitleItem:
    """单条字幕"""
    index: int
    start_time: float    # 秒
    end_time: float      # 秒
    text: str
    style: dict = field(default_factory=lambda: {
        "font": "微软雅黑",
        "size": 48,
        "color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 2,
        "align": "center",
        "position": "bottom",  # bottom / middle / top
    })

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def srt_timestamp(self, seconds: float) -> str:
        ms = int((seconds % 1) * 1000)
        s = int(seconds)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def to_srt_block(self) -> str:
        return (
            f"{self.index}\n"
            f"{self.srt_timestamp(self.start_time)} --> {self.srt_timestamp(self.end_time)}\n"
            f"{self.text}\n"
        )

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "text": self.text,
            "style": self.style,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SubtitleItem":
        return cls(
            index=data["index"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            text=data["text"],
            style=data.get("style", {}),
        )


class SubtitleTrack:
    """字幕轨道 - 管理多条字幕"""

    def __init__(self):
        self._items: list[SubtitleItem] = []
        self._next_index = 1

    @property
    def items(self) -> list[SubtitleItem]:
        return sorted(self._items, key=lambda s: s.start_time)

    def add(self, start_time: float, end_time: float, text: str,
            style: dict = None) -> SubtitleItem:
        item = SubtitleItem(
            index=self._next_index,
            start_time=start_time,
            end_time=end_time,
            text=text,
            style=style or {},
        )
        self._next_index += 1
        self._items.append(item)
        return item

    def remove(self, index: int):
        self._items = [s for s in self._items if s.index != index]

    def update(self, index: int, **kwargs):
        for item in self._items:
            if item.index == index:
                for k, v in kwargs.items():
                    if hasattr(item, k):
                        setattr(item, k, v)
                break

    def move(self, index: int, delta_sec: float):
        """移动字幕时间"""
        for item in self._items:
            if item.index == index:
                item.start_time += delta_sec
                item.end_time += delta_sec
                break

    def clear(self):
        self._items.clear()
        self._next_index = 1

    def to_srt(self) -> str:
        """导出为SRT格式"""
        lines = []
        for item in self.items:
            lines.append(item.to_srt_block())
            lines.append("")
        return "\n".join(lines)

    def from_srt(self, srt_content: str):
        """从SRT文本导入"""
        self.clear()
        blocks = srt_content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            index = int(lines[0].strip())
            time_line = lines[1].strip()
            text = "\n".join(lines[2:]).strip()

            parts = time_line.split(" --> ")
            if len(parts) != 2:
                continue

            start = parse_srt_time(parts[0].strip())
            end = parse_srt_time(parts[1].strip())

            item = SubtitleItem(index=index, start_time=start, end_time=end, text=text)
            self._items.append(item)

        if self._items:
            self._next_index = max(s.index for s in self._items) + 1

    def save_srt(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_srt())

    def load_srt(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.from_srt(f.read())

    def to_dict(self) -> dict:
        return {
            "items": [s.to_dict() for s in self.items],
            "next_index": self._next_index,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SubtitleTrack":
        track = cls()
        track._next_index = data.get("next_index", 1)
        track._items = [SubtitleItem.from_dict(d) for d in data.get("items", [])]
        return track


def parse_srt_time(time_str: str) -> float:
    """解析SRT时间格式 HH:MM:SS,mmm 为秒"""
    time_part, ms_part = time_str.split(",")
    h, m, s = map(int, time_part.split(":"))
    return h * 3600 + m * 60 + s + int(ms_part) / 1000


def generate_ffmpeg_subtitle_filter(srt_path: str, style: dict = None) -> str:
    """生成FFmpeg烧录字幕的滤镜参数"""
    style = style or {}
    font = style.get("font", "微软雅黑")
    size = style.get("size", 48)
    color = style.get("color", "white")
    stroke = style.get("stroke_color", "black")
    stroke_w = style.get("stroke_width", 2)
    align = style.get("align", "center")

    align_map = {"left": 1, "center": 2, "right": 3}
    align_val = align_map.get(align, 2)

    return (
        f"subtitles='{srt_path}'"
        f":force_style='FontName={font},FontSize={size},"
        f"PrimaryColour=&H{color_to_ass(color)},"
        f"OutlineColour=&H{color_to_ass(stroke)},"
        f"Outline={stroke_w},Alignment={align_val}'"
    )


def color_to_ass(hex_color: str) -> str:
    """将 #FFFFFF 转为 ASS 颜色格式（BGR顺序）"""
    hex_color = hex_color.lstrip("#")
    r, g, b = hex_color[:2], hex_color[2:4], hex_color[4:6]
    return f"{b}{g}{r}"
