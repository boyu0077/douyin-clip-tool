"""
视频合成器 - 将时间轴多轨道渲染为最终视频
"""
import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Callable
from config.settings import log, TEMP_DIR, get_ffmpeg_path
from core.timeline_model import TimelineModel
from core.clip import Clip
from processor.ffmpeg_runner import build_ffmpeg_cmd, run_ffmpeg


def compose_timeline(
    timeline: TimelineModel,
    output_path: str,
    resolution: tuple = (1080, 1920),
    progress_callback: Callable[[int], None] = None,
) -> bool:
    """
    将时间轴合成为完整视频

    策略: 使用FFmpeg filter_complex将各轨道片段拼合
    当前版本: 主视频轨道线性拼接 + 音频混音
    """
    video_clips = []
    for track in timeline.tracks.video_tracks:
        if not track.muted:
            video_clips.extend(track.clips)

    if not video_clips:
        log.error("时间轴无视频片段")
        return False

    video_clips.sort(key=lambda c: c.timeline_start)

    # 构建filter_complex
    inputs = []
    filter_parts = []
    concat_inputs = []
    total_duration = 0

    for i, clip in enumerate(video_clips):
        src = clip.source_path
        if not os.path.exists(src):
            continue

        inputs.extend(["-i", src])
        ss = clip.source_start
        dur = clip.source_end - clip.source_start

        filters = [f"[{i}:v]"]
        if ss > 0:
            filters.append(f"trim=start={ss}:duration={dur}")
        filters.append("setpts=PTS-STARTPTS")

        if clip.mirror:
            filters.append("hflip")
        if clip.rotation and abs(clip.rotation) > 0.01:
            filters.append(f"rotate={clip.rotation}*PI/180:fillcolor=black")
        if clip.scale and abs(clip.scale - 1.0) > 0.001:
            filters.append(f"scale=iw*{clip.scale}:ih*{clip.scale}")

        filters.append(f"scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=increase")
        filters.append(f"crop={resolution[0]}:{resolution[1]}")

        filter_parts.append(f"{','.join(filters)}[v{i}]")
        concat_inputs.append(f"[v{i}]")
        total_duration += dur

    # 音频处理
    audio_clips = []
    for track in timeline.tracks.audio_tracks:
        if not track.muted:
            audio_clips.extend(track.clips)
    audio_clips.sort(key=lambda c: c.timeline_start)

    audio_processed = False
    if audio_clips:
        for j, clip in enumerate(audio_clips):
            src = clip.source_path
            if not os.path.exists(src):
                continue
            idx = len(video_clips) + j
            inputs.extend(["-i", src])
            filter_parts.append(
                f"[{idx}:a]atrim=start={clip.source_start}:duration={clip.source_end - clip.source_start},"
                f"volume={clip.volume}[a{j}]"
            )
        audio_concat = "".join(f"[a{j}]" for j in range(len(audio_clips)))
        filter_parts.append(f"{audio_concat}amix=inputs={len(audio_clips)}:duration=longest[aout]")
        audio_processed = True

    # 视频拼接
    concat_str = "".join(concat_inputs)
    filter_parts.append(f"{concat_str}concat=n={len(concat_inputs)}:v=1:a=0[vout]")

    filter_complex = ";".join(filter_parts)

    cmd = [get_ffmpeg_path(), "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
    ]
    if audio_processed:
        cmd += ["-map", "[aout]"]
    cmd += [
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]

    return run_ffmpeg(cmd, progress_callback, total_duration)


def render_subtitle_track(
    video_path: str,
    output_path: str,
    srt_path: str,
    font_size: int = 48,
    font_color: str = "white",
) -> bool:
    """将字幕文件烧录到视频"""
    vf = (
        f"subtitles={srt_path}"
        f":force_style='FontSize={font_size},"
        f"PrimaryColour=&H{font_color[1:] if font_color.startswith('#') else 'FFFFFF'},"
        f"Outline=2,OutlineColour=&H000000,"
        f"Alignment=2,MarginV=60'"
    )
    cmd = build_ffmpeg_cmd(
        input_path=video_path,
        output_path=output_path,
        video_filters=[vf],
    )
    return run_ffmpeg(cmd)
