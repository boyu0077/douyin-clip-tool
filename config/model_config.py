"""
AI模型配置 - 模型路径、下载地址、参数
"""
from dataclasses import dataclass, field
from pathlib import Path
from config.settings import MODELS_DIR


@dataclass
class ModelInfo:
    name: str
    display_name: str
    size_gb: float
    download_url: str
    local_path: Path
    required: bool
    description: str
    installed: bool = False

    def check_installed(self) -> bool:
        return self.local_path.exists()


# 模型清单
MODELS = {
    "yolo": ModelInfo(
        name="yolo",
        display_name="YOLOv8n 物体检测",
        size_gb=0.006,
        download_url="",
        local_path=MODELS_DIR / "yolov8n.pt",
        required=True,
        description="检测画面中的人脸、产品、文字区域",
    ),
    "mediapipe_face": ModelInfo(
        name="mediapipe_face",
        display_name="MediaPipe 人脸跟踪",
        size_gb=0.01,
        download_url="",
        local_path=MODELS_DIR / "face_landmarker.task",
        required=True,
        description="人脸关键点检测与跟踪",
    ),
    "whisper": ModelInfo(
        name="whisper",
        display_name="faster-whisper large-v3",
        size_gb=3.0,
        download_url="",
        local_path=MODELS_DIR / "whisper-large-v3",
        required=False,
        description="语音识别，自动生成字幕时间轴",
    ),
    "qwen_vl": ModelInfo(
        name="qwen_vl",
        display_name="Qwen2.5-VL 7B",
        size_gb=4.0,
        download_url="",
        local_path=MODELS_DIR / "qwen2.5-vl-7b.Q4_K_M.gguf",
        required=False,
        description="视觉场景理解，智能去重策略规划",
    ),
    "qwen_text": ModelInfo(
        name="qwen_text",
        display_name="Qwen2.5 7B",
        size_gb=4.0,
        download_url="",
        local_path=MODELS_DIR / "qwen2.5-7b.Q4_K_M.gguf",
        required=False,
        description="文案生成、标题创作、内容理解",
    ),
}


# Ollama配置
OLLAMA_CONFIG = {
    "host": "http://localhost:11434",
    "models": {
        "vision": "qwen2.5-vl:7b",
        "text": "qwen2.5:7b",
    },
    "keep_alive": "5m",
    "num_gpu_layers": 35,   # GPU推理层数, 根据显存调整
    "context_size": 32768,
    "temperature": 0.1,
}


# YOLO配置
YOLO_CONFIG = {
    "model": "yolov8n.pt",
    "conf_threshold": 0.5,
    "iou_threshold": 0.45,
    "classes_of_interest": [0, 1, 2],  # person, bicycle, car - 可扩展
}


# Whisper配置
WHISPER_CONFIG = {
    "model_size": "large-v3",
    "device": "cuda",       # cuda / cpu
    "compute_type": "float16",
    "beam_size": 5,
    "language": "zh",
    "vad_filter": True,     # 启用语音活动检测
}


def get_required_models() -> list[ModelInfo]:
    """获取必需模型列表（打包内置的）"""
    return [m for m in MODELS.values() if m.required]


def get_optional_models() -> list[ModelInfo]:
    """获取可选模型列表（需下载的）"""
    return [m for m in MODELS.values() if not m.required]


def total_download_size() -> float:
    """计算需要下载的总大小(GB)"""
    return sum(m.size_gb for m in MODELS.values() if not m.required and not m.check_installed())
