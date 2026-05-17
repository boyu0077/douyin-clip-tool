"""去重质量检查 - SSIM/PSNR/感知哈希"""
import json
import subprocess
from pathlib import Path
from config.settings import log, TEMP_DIR, get_ffmpeg_path, get_ffprobe_path
from processor.video_info import get_video_info


def _get_resolution(video_path: str) -> tuple[int, int]:
    """快速获取视频分辨率"""
    info = get_video_info(video_path)
    if info:
        return info.width, info.height
    return 0, 0


def compute_ssim(video1: str, video2: str) -> float:
    """
    比较两个视频的SSIM相似度。
    自动缩放第二个视频以匹配第一个视频的分辨率。
    """
    try:
        w1, h1 = _get_resolution(video1)
        w2, h2 = _get_resolution(video2)
        if w1 == 0 or h1 == 0:
            log.error("无法读取视频分辨率")
            return -1.0

        scale_filter = ""
        if w1 != w2 or h1 != h2:
            scale_filter = f"[1:v]scale={w1}:{h1}:flags=lanczos[scaled];"
            ssim_input = "[0:v][scaled]"
        else:
            ssim_input = "[0:v][1:v]"

        cmd = [
            get_ffmpeg_path(), "-i", video1, "-i", video2,
            "-filter_complex",
            f"{scale_filter}{ssim_input}ssim=stats_file=-",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        for line in result.stderr.split("\n"):
            if "All:" in line:
                parts = line.split("All:")
                if len(parts) == 2:
                    return float(parts[1].strip().split()[0])
        # FFmpeg SSIM 有时输出在 stdout
        for line in result.stdout.split("\n"):
            if "All:" in line:
                parts = line.split("All:")
                if len(parts) == 2:
                    return float(parts[1].strip().split()[0])
    except Exception as e:
        log.error(f"SSIM计算失败: {e}")
    return -1.0


def compute_psnr(video1: str, video2: str) -> float:
    """比较两个视频的PSNR，自动缩放第二个视频"""
    try:
        w1, h1 = _get_resolution(video1)
        if w1 == 0 or h1 == 0:
            return -1.0

        w2, h2 = _get_resolution(video2)
        scale_filter = ""
        if w1 != w2 or h1 != h2:
            scale_filter = f"[1:v]scale={w1}:{h1}:flags=lanczos[scaled];"
            psnr_input = "[0:v][scaled]"
        else:
            psnr_input = "[0:v][1:v]"

        cmd = [
            get_ffmpeg_path(), "-i", video1, "-i", video2,
            "-filter_complex",
            f"{scale_filter}{psnr_input}psnr=stats_file=-",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        for line in result.stderr.split("\n"):
            if "average:" in line:
                parts = line.split("average:")
                if len(parts) == 2:
                    return float(parts[1].strip().split()[0])
        for line in result.stdout.split("\n"):
            if "average:" in line:
                parts = line.split("average:")
                if len(parts) == 2:
                    return float(parts[1].strip().split()[0])
    except Exception as e:
        log.error(f"PSNR计算失败: {e}")
    return -1.0


def compute_pixel_diff(video1: str, video2: str) -> float:
    """
    像素级差异检测 - 截取中间帧对比。
    返回差异百分比(0-100)，越大差异越大。
    """
    try:
        w1, h1 = _get_resolution(video1)
        if w1 == 0 or h1 == 0:
            return -1.0

        # 截取中间帧
        cmd = [
            get_ffmpeg_path(), "-i", video1, "-i", video2,
            "-filter_complex",
            f"[0:v]trim=duration=1[mid1];[1:v]trim=duration=1,scale={w1}:{h1}:flags=lanczos[mid2];"
            f"[mid1][mid2]blend=difference,select=eq(n\\,0)[diff]",
            "-map", "[diff]", "-vframes", "1",
            "-f", "rawvideo", "-pix_fmt", "gray", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode != 0 or len(result.stdout) == 0:
            return -1.0

        import numpy as np
        frame = np.frombuffer(result.stdout, dtype=np.uint8).reshape((h1, w1))
        avg_diff = np.mean(frame) / 255.0 * 100
        return round(avg_diff, 2)
    except Exception as e:
        log.error(f"像素差异计算失败: {e}")
    return -1.0


def check_dedup_quality(original: str, processed: str) -> dict:
    """
    检查去重质量
    SSIM < 0.95 视为差异足够（通过）
    SSIM < 0.85 提示过度处理
    """
    ssim = compute_ssim(original, processed)
    pixel_diff = 0
    if ssim < 0:
        pixel_diff = compute_pixel_diff(original, processed)

    quality = {
        "ssim": round(ssim, 4),
        "psnr": 0,
        "pixel_diff": pixel_diff,
        "passed": False,
        "warning": "",
        "score": 0,
    }

    if ssim < 0 and pixel_diff < 0:
        quality["warning"] = "质量检测失败（分辨率差异过大或编码不兼容）"
        quality["passed"] = True
        quality["score"] = 50
    elif ssim < 0 and pixel_diff >= 0:
        if pixel_diff < 5:
            quality["warning"] = f"像素差异仅{pixel_diff:.1f}%，建议增强去重强度"
            quality["score"] = 30
        elif pixel_diff < 15:
            quality["passed"] = True
            quality["score"] = 75
        else:
            quality["passed"] = True
            quality["warning"] = "画面差异较大，可能处理过度"
            quality["score"] = 60
    elif ssim < 0.85:
        quality["warning"] = "处理过度，画面质量下降明显"
        quality["passed"] = True
        quality["score"] = 60
    elif ssim < 0.95:
        quality["passed"] = True
        quality["score"] = 85
    else:
        quality["warning"] = "与原片相似度过高，建议增强去重强度"
        quality["score"] = 30

    log.info(f"质量检查: SSIM={ssim:.4f}, pix_diff={pixel_diff}%, 通过={quality['passed']}")
    return quality
