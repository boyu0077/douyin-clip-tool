"""
AI模型管理器 - 下载/更新/缓存管理
"""
import os
import threading
from pathlib import Path
from typing import Optional, Callable
from config.model_config import MODELS, ModelInfo, OLLAMA_CONFIG, get_optional_models


class ModelManager:
    """模型生命周期管理"""
    
    def __init__(self):
        self._download_progress: dict[str, float] = {}
        self._download_lock = threading.Lock()
        self.on_progress: Optional[Callable] = None
    
    def get_model_status(self) -> dict[str, bool]:
        """获取所有模型的安装状态"""
        return {name: info.check_installed() for name, info in MODELS.items()}
    
    def is_ready(self, model_name: str) -> bool:
        return model_name in MODELS and MODELS[model_name].check_installed()
    
    def get_optional_status(self) -> dict:
        """获取可选模型状态"""
        return {
            name: {
                "display": info.display_name,
                "size_gb": info.size_gb,
                "installed": info.check_installed(),
                "required": info.required,
            }
            for name, info in MODELS.items()
        }
    
    def check_ollama(self) -> bool:
        """检查Ollama服务是否运行"""
        import requests
        try:
            resp = requests.get(f"{OLLAMA_CONFIG['host']}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False
    
    def pull_ollama_model(self, model_name: str, 
                          progress_cb: Optional[Callable] = None) -> bool:
        """拉取Ollama模型"""
        import requests
        import json
        try:
            resp = requests.post(
                f"{OLLAMA_CONFIG['host']}/api/pull",
                json={"name": model_name, "stream": True},
                stream=True, timeout=10
            )
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    if "completed" in data and "total" in data and progress_cb:
                        progress_cb(data["completed"], data["total"])
                    if data.get("status") == "success":
                        return True
            return False
        except Exception:
            return False
    
    def download_model(self, model_name: str,
                       progress_cb: Optional[Callable] = None) -> bool:
        """下载模型文件"""
        if model_name not in MODELS:
            return False
        
        info = MODELS[model_name]
        if info.check_installed():
            return True
        
        # YOLO模型自动下载
        if model_name == "yolo":
            return self._download_yolo(info, progress_cb)
        
        # Ollama模型通过Ollama拉取
        if model_name in ("qwen_vl", "qwen_text"):
            ollama_name = OLLAMA_CONFIG["models"].get(
                "vision" if model_name == "qwen_vl" else "text"
            )
            return self.pull_ollama_model(ollama_name, progress_cb)
        
        # Whisper模型自动下载
        if model_name == "whisper":
            return self._download_whisper(info, progress_cb)
        
        return False
    
    def _download_yolo(self, info: ModelInfo, progress_cb=None) -> bool:
        """自动下载YOLO模型"""
        try:
            from ultralytics import YOLO
            # YOLO会自动下载到默认位置
            model = YOLO("yolov8n.pt")
            # 复制到我们的模型目录
            import shutil
            default_path = Path.home() / ".ultralytics" / "models" / "yolov8n.pt"
            if default_path.exists():
                info.local_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(default_path, info.local_path)
                return True
            return False
        except Exception:
            return False
    
    def _download_whisper(self, info: ModelInfo, progress_cb=None) -> bool:
        """下载Whisper模型（通过faster-whisper自动缓存）"""
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("large-v3", device="cpu", compute_type="int8")
            # faster-whisper自动下载到cache
            if progress_cb:
                progress_cb(100, 100)
            return True
        except Exception:
            return False
    
    def get_download_size(self) -> float:
        """计算需要下载的总大小(GB)"""
        return sum(
            info.size_gb for name, info in MODELS.items()
            if not info.required and not info.check_installed()
        )
    
    def verify_all(self) -> dict[str, str]:
        """验证所有模型"""
        results = {}
        for name, info in MODELS.items():
            if info.required:
                if not info.check_installed():
                    results[name] = f"缺失: {info.display_name}"
                else:
                    results[name] = "OK"
            else:
                results[name] = "已安装" if info.check_installed() else "未安装(可选)"
        return results


# 全局单例
model_manager = ModelManager()
