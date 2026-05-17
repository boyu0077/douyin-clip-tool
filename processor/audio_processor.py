"""音频处理 - 变速/变调/降噪/混音"""
import numpy as np
import subprocess
from pathlib import Path
from config.settings import log, TEMP_DIR, get_ffmpeg_path

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    log.warning("librosa未安装，部分音频处理功能不可用")

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False
    log.warning("pydub未安装，部分音频处理功能不可用")


def extract_audio(video_path: str, output_path: str = None) -> str:
    """从视频中提取音频为WAV"""
    output_path = output_path or str(TEMP_DIR / f"{Path(video_path).stem}_audio.wav")
    cmd = [
        get_ffmpeg_path(), "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "44100", "-ac", "2",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    if Path(output_path).exists():
        return output_path
    return ""


def combine_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
) -> bool:
    """将新音频合成到视频中"""
    cmd = [
        get_ffmpeg_path(), "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True
    log.error(f"音视频合成失败: {result.stderr}")
    return False


def change_speed_and_pitch(
    audio_path: str,
    speed_factor: float = 1.0,
    pitch_semitones: float = 0.0,
    output_path: str = None,
) -> str:
    """
    变速 + 变调
    speed_factor: 0.95 = 慢5%, 1.05 = 快5%
    pitch_semitones: 正数升调, 负数降调
    """
    output_path = output_path or str(
        TEMP_DIR / f"{Path(audio_path).stem}_speed{pitch_semitones:.2f}.wav"
    )

    if HAS_LIBROSA:
        y, sr = librosa.load(audio_path, sr=None)
        # 变速
        y_stretched = librosa.effects.time_stretch(y, rate=speed_factor)
        # 变调
        if pitch_semitones != 0:
            y_stretched = librosa.effects.pitch_shift(
                y_stretched, sr=sr, n_steps=pitch_semitones
            )
        import soundfile as sf
        sf.write(output_path, y_stretched, sr)
    else:
        # 使用 ffmpeg atempo 降级方案（仅变速）
        atempo = min(max(speed_factor, 0.5), 2.0)
        cmd = [
            get_ffmpeg_path(), "-y", "-i", audio_path,
            "-filter:a", f"atempo={atempo}",
            "-vn", output_path
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    return output_path


def adjust_volume(audio_path: str, db_change: float = 0.0, output_path: str = None) -> str:
    """调整音量，db_change可为正负，单位dB"""
    output_path = output_path or str(
        TEMP_DIR / f"{Path(audio_path).stem}_vol{db_change:.1f}.wav"
    )

    if HAS_PYDUB:
        audio = AudioSegment.from_file(audio_path)
        audio = audio + db_change
        audio.export(output_path, format="wav")
    else:
        volume_filter = f"volume={db_change}dB"
        cmd = [
            get_ffmpeg_path(), "-y", "-i", audio_path,
            "-filter:a", volume_filter,
            "-vn", output_path
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    return output_path


def mix_audio(
    main_audio_path: str,
    bgm_path: str,
    bgm_volume_ratio: float = 0.3,
    output_path: str = None,
) -> str:
    """混合BGM到主音频"""
    output_path = output_path or str(
        TEMP_DIR / f"{Path(main_audio_path).stem}_mixed.wav"
    )

    if HAS_PYDUB:
        main = AudioSegment.from_file(main_audio_path)
        bgm = AudioSegment.from_file(bgm_path)

        # BGM降低音量
        bgm = bgm - (20 * (1 - bgm_volume_ratio))

        # 循环BGM以匹配主音频长度
        if len(bgm) < len(main):
            repeats = len(main) // len(bgm) + 1
            bgm = bgm * repeats
        bgm = bgm[:len(main)]

        # 混合
        mixed = main.overlay(bgm)
        mixed.export(output_path, format="wav")
    else:
        cmd = [
            get_ffmpeg_path(), "-y",
            "-i", main_audio_path,
            "-i", bgm_path,
            "-filter_complex",
            f"[1:a]volume={bgm_volume_ratio}[bgm];[0:a][bgm]amix=inputs=2:duration=first",
            "-vn", output_path
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    return output_path


def reduce_noise(audio_path: str, output_path: str = None) -> str:
    """音频降噪（基于频谱减法）"""
    output_path = output_path or str(
        TEMP_DIR / f"{Path(audio_path).stem}_denoised.wav"
    )

    if HAS_LIBROSA:
        y, sr = librosa.load(audio_path, sr=None)

        # 取前0.5秒作为噪声样本
        noise_sample = y[:int(sr * 0.5)]

        # 计算噪声频谱
        noise_stft = librosa.stft(noise_sample)
        noise_mag = np.abs(noise_stft)
        noise_mean = np.mean(noise_mag, axis=1, keepdims=True)

        # 对全音频做STFT
        y_stft = librosa.stft(y)
        y_mag = np.abs(y_stft)
        y_phase = np.angle(y_stft)

        # 频谱减法
        y_mag_clean = np.maximum(y_mag - noise_mean * 2, 0)
        y_stft_clean = y_mag_clean * np.exp(1j * y_phase)

        # ISTFT
        y_clean = librosa.istft(y_stft_clean, length=len(y))

        import soundfile as sf
        sf.write(output_path, y_clean, sr)
    else:
        # FFmpeg anlmdn 降噪降级方案
        cmd = [
            get_ffmpeg_path(), "-y", "-i", audio_path,
            "-filter:a", "anlmdn=s=0.0001",
            "-vn", output_path
        ]
        subprocess.run(cmd, capture_output=True, text=True)

    return output_path
