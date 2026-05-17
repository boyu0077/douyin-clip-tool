"""
语音识别模块 - faster-whisper转文字 + 生成SRT字幕
"""
import os
from typing import Optional, Callable
from config.model_config import WHISPER_CONFIG


class WhisperTranscriber:
    """语音转文字引擎"""
    
    def __init__(self):
        self.model = None
        self._loaded = False
    
    def _lazy_load(self):
        if self._loaded:
            return
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(
                WHISPER_CONFIG["model_size"],
                device=WHISPER_CONFIG["device"],
                compute_type=WHISPER_CONFIG["compute_type"],
            )
            self._loaded = True
        except Exception as e:
            print(f"[Whisper] 模型加载失败: {e}")
            self.model = None
    
    def transcribe(
        self,
        audio_path: str,
        language: str = "zh",
        progress_cb: Optional[Callable] = None,
    ) -> list[dict]:
        """
        语音转文字
        返回: [{"start": float, "end": float, "text": str}, ...]
        """
        self._lazy_load()
        if not self.model:
            return []
        
        segments_result = []
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=WHISPER_CONFIG["beam_size"],
            vad_filter=True,
        )
        
        for segment in segments:
            segments_result.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            })
            if progress_cb:
                progress_cb(segment.start, segment.end)
        
        return segments_result
    
    def segments_to_srt(self, segments: list[dict]) -> str:
        """将语音段转换为SRT字幕格式"""
        lines = []
        for i, seg in enumerate(segments, 1):
            start = self._format_time(seg["start"])
            end = self._format_time(seg["end"])
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(seg["text"])
            lines.append("")
        return "\n".join(lines)
    
    def _format_time(self, seconds: float) -> str:
        """秒 → SRT时间格式 HH:MM:SS,mmm"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    def save_srt(self, segments: list[dict], output_path: str):
        srt = self.segments_to_srt(segments)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt)


# 全局单例
transcriber = WhisperTranscriber()
