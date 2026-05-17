"""
AI去重策略规划器 - 分析视频内容，生成最优去重方案
"""
import json
from typing import Optional
from config.model_config import OLLAMA_CONFIG


class DedupPlanner:
    """AI去重策略规划"""
    
    def __init__(self):
        self.ollama_host = OLLAMA_CONFIG["host"]
        self.model = OLLAMA_CONFIG["models"]["vision"]
    
    def analyze_and_plan(
        self,
        video_metadata: dict,
        scene_descriptions: list[str],
        detected_objects: list[str],
    ) -> dict:
        """
        基于视频分析结果，生成去重策略
        
        输入:
        - video_metadata: 视频元信息(duration, fps, resolution)
        - scene_descriptions: 场景文字描述
        - detected_objects: 检测到的物体列表
        
        返回:
        - 去重策略JSON
        """
        prompt = f"""你是抖音视频去重策略专家。根据以下视频分析结果，生成最优去重参数。

视频信息:
- 时长: {video_metadata.get('duration', 0):.1f}秒
- 分辨率: {video_metadata.get('video_width', 0)}x{video_metadata.get('video_height', 0)}
- 帧率: {video_metadata.get('video_fps', 0)}

场景描述: {'; '.join(scene_descriptions[:5])}
检测到: {', '.join(detected_objects[:10])}

请输出一个JSON格式的去重策略，包含以下字段:
{{
  "content_type": "口播/带货/混剪/剧情/美食/美妆/游戏/户外/教程/Vlog",
  "spatial": {{"crop_pct": 0.01-0.05, "scale": 0.95-1.05, "mirror": true/false, "rotation": 0.1-2.0}},
  "temporal": {{"speed": 1.0-1.06, "drop_frames": 0-5, "frame_offset": 0-5}},
  "color": {{"brightness": -0.08到0.08, "contrast": -0.10到0.10, "saturation": -0.06到0.12}},
  "effects": {{"blur_edges": true/false, "noise": true/false, "border": true/false, "shake": true/false}},
  "audio": {{"pitch_shift": 0.01-0.06, "volume_db": -2.0到2.0}},
  "reasoning": "策略选择的简短理由"
}}

重要规则:
- 口播/教程类: 不要镜像（文字会反转）,轻度处理,保留人脸清晰
- 带货/美妆类: 打开边框、水印,增强亮度和对比度
- 混剪/游戏类: 大幅去重,开噪点和抖动,高抽帧
- 如有产品特写: 保持该段饱和度,不要加噪点
- 如有大量文字: 不要镜像和旋转

只输出JSON，不要其他文字。"""
        
        try:
            strategy = self._call_ollama(prompt)
            return strategy
        except Exception:
            return self._fallback_strategy(video_metadata)
    
    def _call_ollama(self, prompt: str) -> dict:
        """调用Ollama API"""
        import requests
        resp = requests.post(
            f"{self.ollama_host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 512}
            },
            timeout=60
        )
        if resp.status_code == 200:
            text = resp.json().get("response", "{}")
            # 提取JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        return {}
    
    def _fallback_strategy(self, metadata: dict) -> dict:
        """Ollama不可用时的回退策略"""
        return {
            "content_type": "Vlog",
            "spatial": {"crop_pct": 0.025, "scale": 1.02, "mirror": True, "rotation": 1.0},
            "temporal": {"speed": 1.03, "drop_frames": 2, "frame_offset": 2},
            "color": {"brightness": 0.0, "contrast": 0.0, "saturation": 0.02},
            "effects": {"blur_edges": True, "noise": False, "border": True, "shake": False},
            "audio": {"pitch_shift": 0.03, "volume_db": 1.0},
            "reasoning": "Ollama未连接，使用默认均衡策略"
        }


# 全局单例
planner = DedupPlanner()
