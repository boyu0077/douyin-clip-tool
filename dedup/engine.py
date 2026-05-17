"""
去重引擎总调度 - 协调所有16种变换
"""
import random
import os
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from config.presets import DEDUP_TEMPLATES, DedupPreset
from config.settings import get_ffprobe_path
from processor.ffmpeg_runner import ffmpeg


@dataclass
class DedupConfig:
    """去重配置（序列化友好）"""
    mirror: bool = False
    speed_change: float = 0.0
    crop_pct: float = 0.0
    scale_range: tuple = (1.0, 1.0)
    rotation_range: tuple = (0, 0)
    brightness_range: tuple = (0, 0)
    contrast_range: tuple = (0, 0)
    saturation_range: tuple = (0, 0)
    frame_offset: int = 0
    drop_frames: int = 0
    noise: bool = False
    border: bool = False
    shake: bool = False
    blur_edges: bool = False
    watermark_text: str = ""
    audio_pitch: float = 0.0
    audio_volume_db: float = 0.0
    pip_enabled: bool = False
    pip_scale: float = 0.33
    pip_x: str = "right"
    pip_y: str = "bottom"
    pip_opacity: float = 0.85

    def randomize(self) -> dict:
        """随机化参数（在范围内取随机值）"""
        return {
            "mirror": self.mirror and random.random() > 0.5,
            "speed": 1.0 + self.speed_change,
            "crop_pct": self.crop_pct,
            "scale": random.uniform(*self.scale_range),
            "rotation": random.uniform(*self.rotation_range),
            "brightness": random.uniform(*self.brightness_range),
            "contrast": random.uniform(*self.contrast_range),
            "saturation": random.uniform(*self.saturation_range),
            "frame_offset": self.frame_offset,
            "drop_frames": self.drop_frames,
            "noise": self.noise,
            "border": self.border,
            "shake": self.shake,
            "blur_edges": self.blur_edges,
            "audio_pitch": self.audio_pitch,
            "audio_volume_db": self.audio_volume_db,
            "pip_enabled": self.pip_enabled,
            "pip_scale": self.pip_scale,
            "pip_x": self.pip_x,
            "pip_y": self.pip_y,
            "pip_opacity": self.pip_opacity,
        }

    @classmethod
    def from_preset(cls, preset: DedupPreset) -> "DedupConfig":
        return cls(
            mirror=preset.mirror,
            speed_change=preset.speed_change,
            crop_pct=preset.crop_percent,
            scale_range=preset.scale_range,
            rotation_range=preset.rotation_range,
            brightness_range=preset.brightness_range,
            contrast_range=preset.contrast_range,
            saturation_range=preset.saturation_range,
            frame_offset=preset.frame_offset,
            drop_frames=preset.drop_frames,
            noise=preset.filter_enabled,
            border=preset.border_enabled,
            shake=preset.shake_enabled,
            blur_edges=preset.blur_edges,
            audio_pitch=preset.audio_pitch_change,
            pip_enabled=preset.pip_enabled,
            pip_scale=preset.pip_scale,
            pip_x=preset.pip_x,
            pip_y=preset.pip_y,
            pip_opacity=preset.pip_opacity,
        )


class DedupEngine:
    """去重引擎 - 16种变换协调器"""
    
    def __init__(self):
        self.cancelled = False
    
    def cancel(self):
        self.cancelled = True
    
    def process_video(
        self,
        input_path: str,
        output_path: str,
        preset_name: str = "Vlog去重",
        progress_cb: Optional[Callable] = None,
    ) -> tuple[bool, str]:
        """
        对单个视频执行完整去重流程
        返回: (成功标志, 错误信息或成功消息)
        """
        if self.cancelled:
            return False, "已取消"
        
        preset = DEDUP_TEMPLATES.get(preset_name)
        if not preset:
            return False, f"未找到模板: {preset_name}"
        
        config = DedupConfig.from_preset(preset)
        params = config.randomize()
        
        return self._execute_dedup(input_path, output_path, params, progress_cb)
    
    def process_ai_strategy(
        self,
        input_path: str,
        output_path: str,
        ai_strategy: dict,
        progress_cb: Optional[Callable] = None,
    ) -> tuple[bool, str]:
        """
        使用AI生成的策略执行去重
        ai_strategy: AI推理出的变换参数
        """
        if self.cancelled:
            return False, "已取消"
        return self._execute_dedup(input_path, output_path, ai_strategy, progress_cb)
    
    def _execute_dedup(
        self,
        input_path: str,
        output_path: str,
        params: dict,
        progress_cb: Optional[Callable],
    ) -> tuple[bool, str]:
        """核心去重执行（FFmpeg滤镜链）"""
        
        if not os.path.exists(input_path):
            return False, f"视频文件不存在: {input_path}"
        info = ffmpeg.get_video_info(input_path)
        if not info:
            # 诊断信息
            ffprobe_path = get_ffprobe_path()
            exists = os.path.exists(ffprobe_path) if os.path.exists(ffprobe_path) else False
            return False, f"无法读取视频信息。ffprobe路径={ffprobe_path}, 存在={exists}, 文件={input_path}"
        
        dur = info.get("duration", 0)
        w = info.get("video_width", 1080)
        h = info.get("video_height", 1920)
        
        vf_filters = []
        af_filters = []
        
        # === 1. 帧偏移 ===
        frame_offset = params.get("frame_offset", 0)
        if frame_offset > 0:
            vf_filters.append(f"trim=start_frame={frame_offset},setpts=PTS-STARTPTS")
        
        # === 2. 裁剪 ===
        crop_pct = params.get("crop_pct", 0)
        if crop_pct > 0.001:
            dw = int(w * crop_pct)
            dh = int(h * crop_pct)
            cw, ch = w - 2 * dw, h - 2 * dh
            if cw > 0 and ch > 0:
                vf_filters.append(f"crop={cw}:{ch}:{dw}:{dh}")
        
        # === 3. 缩放（随机波动） ===
        scale_val = params.get("scale", 1.0)
        vf_filters.append(f"scale=iw*{scale_val:.3f}:ih*{scale_val:.3f}:flags=lanczos")
        
        # === 4. 最终缩放到9:16 ===
        vf_filters.append("scale=1080:1920:force_original_aspect_ratio=increase")
        vf_filters.append("crop=1080:1920")
        
        # === 5. 镜像 ===
        if params.get("mirror"):
            vf_filters.append("hflip")
        
        # === 6. 旋转 ===
        rotation = params.get("rotation", 0)
        if abs(rotation) > 0.01:
            vf_filters.append(f"rotate={rotation}*PI/180:fillcolor=black")
        
        # === 7. 色彩调整 ===
        br = params.get("brightness", 0)
        ct = params.get("contrast", 0)
        st = params.get("saturation", 0)
        if abs(br) > 0.001 or abs(ct) > 0.001 or abs(st) > 0.001:
            vf_filters.append(f"eq=brightness={br:.3f}:contrast={1+ct:.3f}:saturation={1+st:.3f}")
        
        # === 8. 噪点 ===
        if params.get("noise"):
            vf_filters.append("noise=alls=3:allf=t")
        
        # === 9. 边缘模糊 ===
        if params.get("blur_edges"):
            vf_filters.append("gblur=sigma=2:steps=1")
        
        # === 10. 动态边框 ===
        if params.get("border"):
            vf_filters.append("pad=iw+8:ih+8:4:4:color=#333333")
        
        # === 11. 画面抖动 ===
        if params.get("shake"):
            vf_filters.append("crop=iw-12:ih-12:6*sin(2*PI*n/30):6*cos(2*PI*n/30)")
        
        # === 12. 抽帧 ===
        drop = params.get("drop_frames", 0)
        if drop > 0:
            target_fps = max(15, int(info.get("video_fps", 30)) - drop)
            vf_filters.append(f"fps={target_fps}")
        
        # === 13. 水印 ===
        watermark = params.get("watermark_text", "")
        if watermark:
            vf_filters.append(
                f"drawtext=text='{watermark}':fontsize=32:fontcolor=white@0.3:"
                f"x=w-tw-20:y=h-th-20:shadowx=2:shadowy=2:shadowcolor=black@0.5"
            )
        
        # === 音频处理 ===
        pitch = params.get("audio_pitch", 0)
        if abs(pitch) > 0.001:
            tempo = 1.0 + pitch
            af_filters.append(f"atempo={tempo:.4f}")
        
        vol = params.get("audio_volume_db", 0)
        if abs(vol) > 0.1:
            af_filters.append(f"volume={vol}dB")
        
        # === 14. 画中画分层（视频分两层） ===
        use_pip = params.get("pip_enabled", False)
        pip_scale = params.get("pip_scale", 0.33)
        pip_x = params.get("pip_x", "right")
        pip_y = params.get("pip_y", "bottom")
        pip_opacity = params.get("pip_opacity", 0.85)

        # === 构建FFmpeg命令 ===
        args = ["-i", input_path]

        # 计算小窗尺寸（相对主画面9:16 = 1080x1920）
        pip_w = int(1080 * pip_scale)
        pip_h = int(1920 * pip_scale)

        # 计算小窗位置
        x_map = {"left": 20, "center": f"(1080-{pip_w})/2", "right": f"1080-{pip_w}-20"}
        y_map = {"top": 20, "middle": f"(1920-{pip_h})/2", "bottom": f"1920-{pip_h}-20"}
        ov_x = x_map.get(pip_x, f"1080-{pip_w}-20")
        ov_y = y_map.get(pip_y, f"1920-{pip_h}-20")

        if use_pip:
            # 使用 filter_complex 实现画中画
            vf_chain = ",".join(vf_filters) if vf_filters else "copy"
            filter_complex = (
                f"[0:v]{vf_chain},split[main][pip];"
                f"[pip]scale={pip_w}:{pip_h},format=rgba,"
                f"colorchannelmixer=aa={pip_opacity}[pip_a];"
                f"[main][pip_a]overlay={ov_x}:{ov_y}[vout]"
            )
            args += ["-filter_complex", filter_complex, "-map", "[vout]"]
        else:
            if vf_filters:
                args += ["-vf", ",".join(vf_filters)]

        if af_filters:
            args += ["-af", ",".join(af_filters)]

        if use_pip:
            args += ["-map", "0:a"]
        args += [
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-movflags", "+faststart",
            "-max_muxing_queue_size", "1024",
            output_path
        ]
        
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        
        if progress_cb:
            progress_cb(0, "开始去重...")
        
        success, output = ffmpeg.run(args)
        
        if success and progress_cb:
            progress_cb(100, "去重完成")
        
        return success, output


# 全局单例
dedup_engine = DedupEngine()
