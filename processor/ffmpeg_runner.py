"""
FFmpeg命令构建与执行器 - 所有视频处理底层通过FFmpeg完成
"""
import subprocess
import os
import json
from pathlib import Path
from typing import Optional
from config.settings import get_ffmpeg_path, get_ffprobe_path


class FFmpegRunner:
    """FFmpeg命令执行器"""

    def __init__(self):
        self._progress_callback = None

    @property
    def ffmpeg(self) -> str:
        return get_ffmpeg_path()

    @property
    def ffprobe(self) -> str:
        return get_ffprobe_path()

    def set_progress_callback(self, callback):
        self._progress_callback = callback

    def run(self, args: list[str], progress: bool = True) -> tuple[bool, str]:
        """
        执行FFmpeg命令
        返回: (成功标志, 错误信息/日志)
        """
        cmd = [self.ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
        if progress:
            cmd += ["-progress", "pipe:1", "-nostats"]
        cmd += args

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            stdout, stderr = process.communicate()

            if process.returncode != 0:
                return False, stderr or "FFmpeg执行失败"

            return True, stdout
        except FileNotFoundError:
            return False, f"FFmpeg未找到: {self.ffmpeg}"
        except Exception as e:
            return False, str(e)

    def get_video_info(self, filepath: str) -> dict:
        """获取视频元信息"""
        cmd = [
            self.ffprobe, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", filepath
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {}
            info = json.loads(result.stdout)
            
            video_stream = None
            audio_stream = None
            for s in info.get("streams", []):
                if s["codec_type"] == "video" and not video_stream:
                    video_stream = s
                elif s["codec_type"] == "audio" and not audio_stream:
                    audio_stream = s
            
            fmt = info.get("format", {})
            return {
                "duration": float(fmt.get("duration", 0)),
                "size_bytes": int(fmt.get("size", 0)),
                "video_codec": video_stream.get("codec_name", "") if video_stream else "",
                "video_width": video_stream.get("width", 0) if video_stream else 0,
                "video_height": video_stream.get("height", 0) if video_stream else 0,
                "video_fps": eval(video_stream.get("r_frame_rate", "0")) if video_stream else 0,
                "video_bitrate": int(video_stream.get("bit_rate", 0)) if video_stream else 0,
                "audio_codec": audio_stream.get("codec_name", "") if audio_stream else "",
                "audio_sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
                "audio_channels": audio_stream.get("channels", 0) if audio_stream else 0,
            }
        except Exception:
            return {}
    
    # ========== 滤镜构建 ==========
    
    def build_vf_chain(self, filters: list[str]) -> str:
        """构建视频滤镜链"""
        return ",".join(f for f in filters if f)
    
    def build_af_chain(self, filters: list[str]) -> str:
        """构建音频滤镜链"""
        return ",".join(f for f in filters if f)
    
    # ========== 常用操作 ==========
    
    def trim_video(self, input_path: str, output_path: str,
                   start: float, duration: float) -> tuple[bool, str]:
        """裁剪视频片段"""
        return self.run([
            "-ss", str(start), "-i", input_path,
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "ultrafast",
            "-crf", "18", "-c:a", "aac",
            output_path
        ])
    
    def concat_videos(self, input_list_path: str, output_path: str) -> tuple[bool, str]:
        """拼接视频（需提供文件列表txt）"""
        return self.run([
            "-f", "concat", "-safe", "0", "-i", input_list_path,
            "-c", "copy", output_path
        ])
    
    def scale_to_9_16(self, input_path: str, output_path: str) -> tuple[bool, str]:
        """缩放到9:16竖屏（居中裁剪）"""
        return self.run([
            "-i", input_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ])
    
    def render_subtitles(self, input_path: str, output_path: str,
                         srt_path: str, font_size: int = 48,
                         font_color: str = "white") -> tuple[bool, str]:
        """渲染字幕到视频"""
        vf = (
            f"subtitles={srt_path}"
            f":force_style='FontSize={font_size},"
            f"PrimaryColour=&H{font_color[1:] if font_color.startswith('#') else 'FFFFFF'},"
            f"Outline=2,OutlineColour=&H000000,"
            f"Alignment=2,MarginV=60'"
        )
        return self.run([
            "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "copy",
            output_path
        ])
    
    def mix_audio(self, video_path: str, bgm_path: str,
                  output_path: str, bgm_volume: float = 0.3) -> tuple[bool, str]:
        """混入BGM"""
        af = (
            f"[1:a]volume={bgm_volume},afade=t=in:d=0.5,afade=t=out:d=1.0[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2"
        )
        return self.run([
            "-i", video_path, "-i", bgm_path,
            "-filter_complex", af,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", output_path
        ])

# 全局单例
ffmpeg = FFmpegRunner()


def build_ffmpeg_cmd(
    input_path: str,
    output_path: str,
    start_time: float = None,
    duration: float = None,
    video_filters: list[str] = None,
    audio_filters: list[str] = None,
    video_bitrate: str = "10M",
    audio_bitrate: str = "192k",
    width: int = None,
    height: int = None,
    fps: int = None,
) -> list[str]:
    """构建FFmpeg命令（独立函数，供editor/exporter调用）"""
    cmd = [get_ffmpeg_path(), "-y"]

    if start_time is not None:
        cmd += ["-ss", str(start_time)]
    cmd += ["-i", input_path]
    if duration is not None:
        cmd += ["-t", str(duration)]

    vf_parts = []
    if video_filters:
        vf_parts.extend(video_filters)
    if width and height:
        vf_parts.append(f"scale={width}:{height}")
    if vf_parts:
        cmd += ["-vf", ",".join(vf_parts)]
    if audio_filters:
        cmd += ["-af", ",".join(audio_filters)]

    cmd += [
        "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p",
    ]
    if video_bitrate:
        cmd += ["-b:v", video_bitrate]
    cmd += ["-c:a", "aac"]
    if audio_bitrate:
        cmd += ["-b:a", audio_bitrate]
    if fps:
        cmd += ["-r", str(fps)]
    cmd += ["-movflags", "+faststart", output_path]
    return cmd


def run_ffmpeg(
    cmd: list[str],
    progress_callback=None,
    total_duration: float = 0,
) -> bool:
    """执行FFmpeg命令（独立函数，支持进度回调）"""
    import re
    # 注入进度输出
    full_cmd = [get_ffmpeg_path(), "-y", "-hide_banner", "-loglevel", "error"]
    if progress_callback and total_duration > 0:
        full_cmd += ["-progress", "pipe:1", "-nostats"]
    full_cmd += cmd[1:]  # skip leading ffmpeg path from build_ffmpeg_cmd

    try:
        process = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        for line in process.stdout:
            if progress_callback and total_duration > 0:
                m = re.search(r"out_time=(\d+):(\d+):(\d+)\.(\d+)", line)
                if m:
                    h, mi, s, cs = map(int, m.groups())
                    current = h * 3600 + mi * 60 + s + cs / 100
                    progress_callback(current / total_duration * 100)

        process.wait()
        return process.returncode == 0
    except Exception:
        return False


def detect_hw_encoder() -> str:
    """检测可用硬件编码器"""
    try:
        result = subprocess.run(
            [get_ffmpeg_path(), "-hide_banner", "-encoders"],
            capture_output=True, text=True,
        )
        encoders = result.stdout
        if "h264_videotoolbox" in encoders:
            return "h264_videotoolbox"
        if "h264_amf" in encoders:
            return "h264_amf"
        if "h264_nvenc" in encoders:
            return "h264_nvenc"
    except Exception:
        pass
    return "libx264"
