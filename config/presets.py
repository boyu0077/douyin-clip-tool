"""
预设模板 - 10种去重模板 + 导出格式预设 + 剪辑模板
"""
from dataclasses import dataclass, field
from typing import Optional


# ============ 去重模板（10种场景化模板）============

@dataclass
class DedupPreset:
    """去重模板定义"""
    name: str
    description: str           # 适用场景说明
    mirror: bool
    speed_change: float        # 变速比例
    crop_percent: float        # 裁剪百分比
    scale_range: tuple         # 缩放范围
    rotation_range: tuple      # 旋转角度范围
    brightness_range: tuple    # 亮度调整范围
    contrast_range: tuple      # 对比度范围
    saturation_range: tuple    # 饱和度范围
    frame_offset: int          # 帧偏移量
    drop_frames: int           # 每秒抽帧数
    border_enabled: bool
    watermark_enabled: bool
    filter_enabled: bool       # 噪点滤镜
    shake_enabled: bool
    blur_edges: bool
    audio_pitch_change: float
    pip_enabled: bool = False     # 画中画分层
    pip_scale: float = 0.33       # 画中画小窗比例
    pip_x: str = "right"          # 小窗X位置: left/center/right
    pip_y: str = "bottom"         # 小窗Y位置: top/middle/bottom
    pip_opacity: float = 0.85     # 小窗不透明度

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "mirror": self.mirror,
            "speed_change": self.speed_change,
            "crop_percent": self.crop_percent,
            "scale": self.scale_range,
            "rotation": self.rotation_range,
            "brightness": self.brightness_range,
            "contrast": self.contrast_range,
            "saturation": self.saturation_range,
            "frame_offset": self.frame_offset,
            "drop_frames": self.drop_frames,
            "border": self.border_enabled,
            "watermark": self.watermark_enabled,
            "filter": self.filter_enabled,
            "shake": self.shake_enabled,
            "blur_edges": self.blur_edges,
            "audio_pitch": self.audio_pitch_change,
        }


DEDUP_TEMPLATES = {
    "口播去重": DedupPreset(
        name="口播去重",
        description="单人说话视频，重点保护人脸区域，轻微变速+色彩微调",
        mirror=False,
        speed_change=0.02,
        crop_percent=0.015,
        scale_range=(0.99, 1.01),
        rotation_range=(-0.3, 0.3),
        brightness_range=(-0.02, 0.03),
        contrast_range=(-0.04, 0.04),
        saturation_range=(-0.02, 0.02),
        frame_offset=2,
        drop_frames=0,
        border_enabled=False,
        watermark_enabled=False,
        filter_enabled=False,
        shake_enabled=False,
        blur_edges=True,
        audio_pitch_change=0.02,
    ),
    "带货去重": DedupPreset(
        name="带货去重",
        description="产品展示类视频，动态边框+水印+亮度增强，突出商品",
        mirror=True,
        speed_change=0.03,
        crop_percent=0.025,
        scale_range=(0.97, 1.03),
        rotation_range=(-1.0, 1.0),
        brightness_range=(0.02, 0.08),
        contrast_range=(0.02, 0.08),
        saturation_range=(0.03, 0.08),
        frame_offset=2,
        drop_frames=1,
        border_enabled=True,
        watermark_enabled=True,
        filter_enabled=False,
        shake_enabled=False,
        blur_edges=True,
        audio_pitch_change=0.03,
    ),
    "混剪去重": DedupPreset(
        name="混剪去重",
        description="多片段混剪视频，高抽帧+帧偏移+旋转，破坏原视频指纹",
        mirror=True,
        speed_change=0.05,
        crop_percent=0.04,
        scale_range=(0.95, 1.05),
        rotation_range=(-2.0, 2.0),
        brightness_range=(-0.04, 0.04),
        contrast_range=(-0.08, 0.08),
        saturation_range=(-0.05, 0.05),
        frame_offset=4,
        drop_frames=4,
        border_enabled=True,
        watermark_enabled=True,
        filter_enabled=True,
        shake_enabled=True,
        blur_edges=True,
        audio_pitch_change=0.05,
    ),
    "剧情去重": DedupPreset(
        name="剧情去重",
        description="剧情类短视频，镜像+中度裁剪+画面抖动+色彩增强",
        mirror=True,
        speed_change=0.03,
        crop_percent=0.03,
        scale_range=(0.98, 1.02),
        rotation_range=(-1.5, 1.5),
        brightness_range=(-0.04, 0.06),
        contrast_range=(-0.08, 0.10),
        saturation_range=(-0.04, 0.06),
        frame_offset=3,
        drop_frames=2,
        border_enabled=False,
        watermark_enabled=False,
        filter_enabled=False,
        shake_enabled=True,
        blur_edges=False,
        audio_pitch_change=0.04,
    ),
    "美食去重": DedupPreset(
        name="美食去重",
        description="美食拍摄视频，增强饱和度+亮度+镜像+暖色滤镜倾向",
        mirror=True,
        speed_change=0.02,
        crop_percent=0.02,
        scale_range=(0.99, 1.02),
        rotation_range=(-0.5, 0.5),
        brightness_range=(0.04, 0.10),
        contrast_range=(0.03, 0.08),
        saturation_range=(0.06, 0.12),
        frame_offset=1,
        drop_frames=2,
        border_enabled=False,
        watermark_enabled=False,
        filter_enabled=True,
        shake_enabled=False,
        blur_edges=True,
        audio_pitch_change=0.02,
    ),
    "美妆去重": DedupPreset(
        name="美妆去重",
        description="美妆教程/展示，柔光效果+对比度增强+边缘模糊+水印",
        mirror=True,
        speed_change=0.03,
        crop_percent=0.02,
        scale_range=(0.98, 1.02),
        rotation_range=(-0.8, 0.8),
        brightness_range=(0.03, 0.07),
        contrast_range=(0.01, 0.06),
        saturation_range=(-0.03, 0.04),
        frame_offset=2,
        drop_frames=1,
        border_enabled=True,
        watermark_enabled=True,
        filter_enabled=False,
        shake_enabled=False,
        blur_edges=True,
        audio_pitch_change=0.03,
    ),
    "游戏去重": DedupPreset(
        name="游戏去重",
        description="游戏录屏，高抽帧+快速变速+噪点+大幅帧偏移",
        mirror=False,
        speed_change=0.05,
        crop_percent=0.03,
        scale_range=(0.96, 1.04),
        rotation_range=(-1.5, 1.5),
        brightness_range=(-0.06, 0.06),
        contrast_range=(-0.10, 0.10),
        saturation_range=(-0.06, 0.06),
        frame_offset=5,
        drop_frames=5,
        border_enabled=True,
        watermark_enabled=True,
        filter_enabled=True,
        shake_enabled=True,
        blur_edges=False,
        audio_pitch_change=0.05,
    ),
    "户外去重": DedupPreset(
        name="户外去重",
        description="户外拍摄，亮度补偿+色彩增强+裁剪+缩放，适应各种光线",
        mirror=False,
        speed_change=0.02,
        crop_percent=0.03,
        scale_range=(0.98, 1.03),
        rotation_range=(-1.0, 1.0),
        brightness_range=(-0.04, 0.08),
        contrast_range=(-0.05, 0.08),
        saturation_range=(0.02, 0.08),
        frame_offset=2,
        drop_frames=2,
        border_enabled=False,
        watermark_enabled=False,
        filter_enabled=False,
        shake_enabled=False,
        blur_edges=True,
        audio_pitch_change=0.02,
    ),
    "教程去重": DedupPreset(
        name="教程去重",
        description="知识教程类，极轻度处理+水印+边缘模糊，保留文字清晰度",
        mirror=False,
        speed_change=0.01,
        crop_percent=0.01,
        scale_range=(0.99, 1.01),
        rotation_range=(-0.3, 0.3),
        brightness_range=(-0.02, 0.02),
        contrast_range=(-0.03, 0.03),
        saturation_range=(-0.01, 0.01),
        frame_offset=1,
        drop_frames=0,
        border_enabled=False,
        watermark_enabled=True,
        filter_enabled=False,
        shake_enabled=False,
        blur_edges=True,
        audio_pitch_change=0.01,
    ),
    "Vlog去重": DedupPreset(
        name="Vlog去重",
        description="日常Vlog，综合均衡处理+动态边框+轻微抖动+色彩微调",
        mirror=True,
        speed_change=0.03,
        crop_percent=0.025,
        scale_range=(0.98, 1.02),
        rotation_range=(-1.0, 1.0),
        brightness_range=(-0.03, 0.05),
        contrast_range=(-0.05, 0.07),
        saturation_range=(-0.03, 0.05),
        frame_offset=2,
        drop_frames=2,
        border_enabled=True,
        watermark_enabled=False,
        filter_enabled=False,
        shake_enabled=True,
        blur_edges=True,
        audio_pitch_change=0.03,
    ),
    "画中画去重": DedupPreset(
        name="画中画去重",
        description="视频分两层：主画面+右下小窗，大幅改变画面指纹",
        mirror=True,
        speed_change=0.02,
        crop_percent=0.01,
        scale_range=(0.99, 1.01),
        rotation_range=(-0.5, 0.5),
        brightness_range=(-0.02, 0.03),
        contrast_range=(-0.04, 0.04),
        saturation_range=(0.01, 0.05),
        frame_offset=2,
        drop_frames=1,
        border_enabled=False,
        watermark_enabled=False,
        filter_enabled=False,
        shake_enabled=False,
        blur_edges=True,
        audio_pitch_change=0.02,
        pip_enabled=True,
        pip_scale=0.33,
        pip_x="right",
        pip_y="bottom",
        pip_opacity=0.85,
    ),
}

# 旧版兼容：强度映射到最接近的模板
DEDUP_PRESETS = {
    "低": DEDUP_TEMPLATES["教程去重"],
    "中": DEDUP_TEMPLATES["Vlog去重"],
    "高": DEDUP_TEMPLATES["混剪去重"],
}


# ============ 导出格式预设 ============

@dataclass
class ExportPreset:
    name: str
    width: int
    height: int
    fps: int
    video_bitrate: str
    audio_bitrate: str
    codec: str
    aspect_ratio: str

    def ffmpeg_args(self) -> dict:
        return {
            "vcodec": "libx264" if self.codec == "h264" else self.codec,
            "acodec": "aac",
            "video_bitrate": self.video_bitrate,
            "audio_bitrate": self.audio_bitrate,
            "s": f"{self.width}x{self.height}",
            "r": self.fps,
            "pix_fmt": "yuv420p",
        }


EXPORT_PRESETS = {
    "抖音竖屏1080P": ExportPreset(
        name="抖音竖屏1080P",
        width=1080, height=1920,
        fps=30, video_bitrate="10M",
        audio_bitrate="192k",
        codec="h264",
        aspect_ratio="9:16"
    ),
    "抖音竖屏720P": ExportPreset(
        name="抖音竖屏720P",
        width=720, height=1280,
        fps=30, video_bitrate="5M",
        audio_bitrate="128k",
        codec="h264",
        aspect_ratio="9:16"
    ),
    "通用横屏1080P": ExportPreset(
        name="通用横屏1080P",
        width=1920, height=1080,
        fps=30, video_bitrate="12M",
        audio_bitrate="192k",
        codec="h264",
        aspect_ratio="16:9"
    ),
    "通用横屏720P": ExportPreset(
        name="通用横屏720P",
        width=1280, height=720,
        fps=30, video_bitrate="6M",
        audio_bitrate="128k",
        codec="h264",
        aspect_ratio="16:9"
    ),
}


# ============ 剪辑模板 ============

@dataclass
class EditTemplate:
    """剪辑项目模板"""
    name: str
    resolution: tuple
    fps: int
    default_transition: str
    default_duration: float
    intro_template: str
    outro_template: str
    subtitle_style: dict


EDIT_TEMPLATES = {
    "带货模板": EditTemplate(
        name="带货模板",
        resolution=(1080, 1920),
        fps=30,
        default_transition="dissolve",
        default_duration=3.0,
        intro_template="产品片头",
        outro_template="引导关注片尾",
        subtitle_style={"font": "微软雅黑", "size": 48, "color": "#FFFFFF", "stroke": "#000000"},
    ),
    "口播模板": EditTemplate(
        name="口播模板",
        resolution=(1080, 1920),
        fps=30,
        default_transition="cut",
        default_duration=2.0,
        intro_template="",
        outro_template="",
        subtitle_style={"font": "微软雅黑", "size": 56, "color": "#FFFF00", "stroke": "#000000"},
    ),
}
