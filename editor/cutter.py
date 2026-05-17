"""切割引擎 - 视频切割合并"""
import subprocess
import json
from pathlib import Path
from typing import Optional, Callable
from config.settings import log, TEMP_DIR, get_ffmpeg_path
from processor.ffmpeg_runner import run_ffmpeg, build_ffmpeg_cmd


def cut_clip(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    re_encode: bool = True,
    progress_callback: Callable[[int], None] = None,
) -> bool:
    """
    从视频中切割片段

    Args:
        input_path: 源视频
        output_path: 输出路径
        start_time: 起始时间(秒)
        end_time: 结束时间(秒)
        re_encode: 是否重新编码（True保证精确切割）
        progress_callback: 进度回调
    """
    duration = end_time - start_time

    if re_encode:
        cmd = build_ffmpeg_cmd(
            input_path=input_path,
            output_path=output_path,
            start_time=start_time,
            duration=duration,
        )
        return run_ffmpeg(cmd, progress_callback, duration)
    else:
        # 流拷贝方式（快速但不精确）
        cmd = [
            get_ffmpeg_path(), "-y",
            "-ss", str(start_time),
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            output_path
        ]
        return run_ffmpeg(cmd, progress_callback, duration)


def merge_videos_fast(
    video_list: list[str],
    output_path: str,
    progress_callback: Callable[[int], None] = None,
) -> bool:
    """快速合并多个视频文件（同编码格式）"""
    concat_file = TEMP_DIR / "merge_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in video_list:
            f.write(f"file '{v}'\n")

    cmd = [
        get_ffmpeg_path(), "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        output_path
    ]
    return run_ffmpeg(cmd, progress_callback)


def merge_videos_with_transition(
    video_list: list[str],
    output_path: str,
    transition_type: str = "fade",
    transition_duration: float = 0.5,
    progress_callback: Callable[[int], None] = None,
) -> bool:
    """带转场效果的视频合并"""
    if len(video_list) == 1:
        import shutil
        shutil.copy(video_list[0], output_path)
        return True

    # 构建复杂滤镜图
    filter_parts = []
    label_parts = []

    for i, v in enumerate(video_list):
        filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}]")
        label_parts.append(f"[v{i}]")

    if transition_type == "fade":
        # 淡入淡出
        filter_parts.append(
            f"{''.join(label_parts)}"
            f"xfade=transition=fade:duration={transition_duration}:offset=0"
        )
    elif transition_type == "dissolve":
        filter_parts.append(
            f"{''.join(label_parts)}"
            f"xfade=transition=dissolve:duration={transition_duration}:offset=0"
        )
    else:
        # 硬切
        filter_parts.append(f"{''.join(label_parts)}concat=n={len(video_list)}:v=1:a=0")

    cmd = [get_ffmpeg_path(), "-y"]
    for v in video_list:
        cmd += ["-i", v]

    cmd += [
        "-filter_complex", ";".join(filter_parts),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        output_path
    ]
    return run_ffmpeg(cmd, progress_callback)


def extract_segments(
    input_path: str,
    segments: list[dict],  # [{"start": 0, "end": 5}, ...]
    output_dir: str = None,
    re_encode: bool = False,
) -> list[str]:
    """从视频提取多个片段"""
    output_dir = output_dir or str(TEMP_DIR / "segments")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    outputs = []
    stem = Path(input_path).stem

    for i, seg in enumerate(segments):
        out_path = f"{output_dir}/{stem}_seg{i + 1}.mp4"
        success = cut_clip(
            input_path, out_path,
            seg["start"], seg["end"],
            re_encode=re_encode,
        )
        if success:
            outputs.append(out_path)

    return outputs
