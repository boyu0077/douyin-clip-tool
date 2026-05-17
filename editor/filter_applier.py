"""
滤镜应用器 - 预设滤镜/自定义滤镜效果
"""
import os
from pathlib import Path
from typing import Optional, Callable
from config.settings import log
from processor.ffmpeg_runner import build_ffmpeg_cmd, run_ffmpeg


# 预设滤镜链
PRESET_FILTERS = {
    "电影感": "eq=contrast=1.1:brightness=0.05:saturation=1.2,unsharp=3:3:1.0",
    "日系清新": "eq=brightness=0.08:saturation=0.85:contrast=0.95",
    "复古": "eq=contrast=0.9:brightness=-0.03:saturation=0.7,noise=alls=5:allf=t",
    "黑白": "hue=s=0",
    "暖色调": "eq=gamma=1.05:brightness=0.03:saturation=1.1",
    "冷色调": "eq=gamma=0.95:brightness=-0.02:saturation=0.9",
    "锐化": "unsharp=5:5:1.5:5:5:0.0",
    "柔焦": "gblur=sigma=1.5,eq=contrast=1.05:brightness=0.02",
    "LUT-暖日": "eq=gamma_r=1.05:gamma_g=0.95:gamma_b=0.85:saturation=1.1",
    "LUT-电影青": "eq=gamma_r=0.90:gamma_g=0.95:gamma_b=1.05:contrast=1.1",
}


def apply_filter(
    input_path: str,
    output_path: str,
    filter_name: str = "电影感",
    intensity: float = 1.0,
    progress_callback: Optional[Callable] = None,
) -> bool:
    """应用预设滤镜到视频"""
    filter_chain = PRESET_FILTERS.get(filter_name)
    if not filter_chain:
        log.error(f"未知滤镜: {filter_name}")
        return False

    # intensity调整（0.5~2.0）
    if intensity != 1.0 and "eq=" in filter_chain:
        filter_chain = filter_chain.replace("eq=", f"eq=")
        # 简单处理: 将强度系数应用到contrast/brightness/saturation
        import re

        def scale_eq(match):
            key = match.group(1)
            val = float(match.group(2))
            if key in ("contrast", "saturation"):
                val = 1.0 + (val - 1.0) * intensity
            else:
                val *= intensity
            return f"{key}={val:.2f}"

        filter_chain = re.sub(r"([a-z]+)=(-?[\d.]+)", scale_eq, filter_chain)

    cmd = build_ffmpeg_cmd(
        input_path=input_path,
        output_path=output_path,
        video_filters=[filter_chain],
    )
    return run_ffmpeg(cmd, progress_callback)


def apply_lut(
    input_path: str,
    output_path: str,
    lut_path: str,
) -> bool:
    """应用3D LUT文件"""
    cmd = build_ffmpeg_cmd(
        input_path=input_path,
        output_path=output_path,
        video_filters=[f"lut3d={lut_path}"],
    )
    return run_ffmpeg(cmd)


def apply_custom_filter(
    input_path: str,
    output_path: str,
    vf_chain: str,
    progress_callback: Optional[Callable] = None,
) -> bool:
    """应用自定义滤镜链"""
    cmd = build_ffmpeg_cmd(
        input_path=input_path,
        output_path=output_path,
        video_filters=[vf_chain],
    )
    return run_ffmpeg(cmd, progress_callback)
