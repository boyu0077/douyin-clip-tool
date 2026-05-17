"""
转场渲染器 - 支持多种转场效果
"""
import os
import subprocess
from pathlib import Path
from typing import Optional, Callable
from config.settings import log, TEMP_DIR, get_ffmpeg_path


TRANSITION_TYPES = {
    "fade": "fade",
    "dissolve": "dissolve",
    "wipeleft": "wipeleft",
    "wiperight": "wiperight",
    "wipeup": "wipeup",
    "wipedown": "wipedown",
    "slideleft": "slideleft",
    "slideright": "slideright",
    "slideup": "slideup",
    "slidedown": "slidedown",
    "circlecrop": "circlecrop",
    "rectcrop": "rectcrop",
    "distance": "distance",
    "fadeblack": "fadeblack",
    "fadewhite": "fadewhite",
    "hlslack": "hlslack",
    "hslack": "hslack",
}


def render_transition(
    input_a: str,
    input_b: str,
    output_path: str,
    transition_type: str = "fade",
    duration: float = 0.5,
    offset: float = 0,
    progress_callback: Optional[Callable] = None,
) -> bool:
    """
    在两个视频之间添加转场效果

    Args:
        input_a: 前一段视频
        input_b: 后一段视频
        output_path: 输出路径
        transition_type: 转场类型
        duration: 转场时长(秒)
        offset: 转场开始偏移量(相对第一个视频尾部)
    """
    xfade_type = TRANSITION_TYPES.get(transition_type, "fade")

    cmd = [
        get_ffmpeg_path(), "-y",
        "-i", input_a,
        "-i", input_b,
        "-filter_complex",
        f"[0:v][1:v]xfade=transition={xfade_type}:duration={duration}:offset={offset}[v]",
        "-map", "[v]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-an",
        "-movflags", "+faststart",
        output_path
    ]

    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode == 0:
        return True
    log.error(f"转场渲染失败: {process.stderr}")
    return False


def render_transition_chain(
    video_list: list[str],
    output_path: str,
    transition_type: str = "fade",
    transition_duration: float = 0.5,
    progress_callback: Optional[Callable] = None,
) -> bool:
    """为多个视频段添加连续转场效果"""
    if len(video_list) < 2:
        if len(video_list) == 1:
            import shutil
            shutil.copy(video_list[0], output_path)
            return True
        return False

    xfade_type = TRANSITION_TYPES.get(transition_type, "fade")

    # 构建多层xfade滤镜图
    inputs = []
    filter_parts = []

    for i, v in enumerate(video_list):
        inputs.extend(["-i", v])
        filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}]")

    # 链式xfade
    current = "[v0]"
    for i in range(len(video_list) - 1):
        next_label = f"x{i}"
        filter_parts.append(
            f"{current}[v{i + 1}]xfade=transition={xfade_type}:"
            f"duration={transition_duration}:offset=0[{next_label}]"
        )
        current = f"[{next_label}]"

    filter_complex = ";".join(filter_parts)

    cmd = [get_ffmpeg_path(), "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", current,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-an",
        "-movflags", "+faststart",
        output_path
    ]

    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode == 0:
        return True
    log.error(f"转场链渲染失败: {process.stderr}")
    return False
