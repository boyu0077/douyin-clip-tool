"""导出引擎 - 视频编码封装输出"""
import subprocess
from pathlib import Path
from typing import Callable, Optional
from config.settings import log, TEMP_DIR
from config.presets import EXPORT_PRESETS, ExportPreset
from processor.ffmpeg_runner import build_ffmpeg_cmd, run_ffmpeg, detect_hw_encoder
from processor.video_info import get_video_info


def export_video(
    input_path: str,
    output_path: str,
    preset_name: str = "抖音竖屏1080P",
    custom_width: int = None,
    custom_height: int = None,
    custom_fps: int = None,
    custom_bitrate: str = None,
    add_watermark: bool = False,
    watermark_text: str = "",
    burn_subtitle: str = None,  # SRT文件路径
    progress_callback: Callable[[int], None] = None,
) -> bool:
    """
    导出视频

    Args:
        input_path: 源视频路径
        output_path: 输出路径
        preset_name: 预设名称
        custom_width/height: 自定义分辨率
        custom_fps: 自定义帧率
        custom_bitrate: 自定义码率
        add_watermark: 是否加水印
        watermark_text: 水印文字
        burn_subtitle: 字幕文件路径（烧录到视频）
        progress_callback: 进度回调
    """
    preset = EXPORT_PRESETS.get(preset_name)

    if preset is None:
        log.error(f"未知导出预设: {preset_name}")
        return False

    info = get_video_info(input_path)
    if info is None:
        log.error("无法读取视频信息")
        return False

    width = custom_width or preset.width
    height = custom_height or preset.height
    fps = custom_fps or preset.fps
    bitrate = custom_bitrate or preset.video_bitrate

    # 横屏转竖屏处理
    video_filters = []
    if info.is_portrait and width < height:
        # 竖屏输出，源视频可能是横屏
        if not info.is_portrait:
            # 横屏转竖屏：裁剪中心区域
            target_ratio = width / height
            src_ratio = info.width / info.height
            if src_ratio > target_ratio:
                # 源更宽，裁两边
                new_w = int(info.height * target_ratio)
                dx = (info.width - new_w) // 2
                video_filters.append(f"crop={new_w}:{info.height}:{dx}:0")
            video_filters.append(f"scale={width}:{height}")

    # 烧录字幕
    if burn_subtitle and Path(burn_subtitle).exists():
        sub_path = Path(burn_subtitle).as_posix().replace(":", "\\\\:")
        video_filters.append(f"subtitles='{sub_path}'")

    # 水印
    if add_watermark and watermark_text:
        font_size = max(24, height // 20)
        video_filters.append(
            f"drawtext=text='{watermark_text}':"
            f"fontsize={font_size}:fontcolor=white@0.3:"
            f"x=(w-text_w)/2:y=h-text_h-30"
        )

    cmd = build_ffmpeg_cmd(
        input_path=input_path,
        output_path=output_path,
        video_filters=video_filters if video_filters else None,
        video_bitrate=bitrate,
        audio_bitrate=preset.audio_bitrate,
        width=width,
        height=height,
        fps=fps,
    )

    def progress_wrapper(percent: float):
        if progress_callback:
            progress_callback(int(percent))

    return run_ffmpeg(cmd, progress_wrapper, info.duration)
