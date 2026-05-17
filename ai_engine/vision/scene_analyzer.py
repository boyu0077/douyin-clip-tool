"""AI视觉分析 - 场景理解 + 物体检测"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from config.settings import log, TEMP_DIR, app_config
from config.model_config import YOLO_CONFIG
from processor.video_info import get_video_info


class SceneAnalyzer:
    """场景分析器 - 采样关键帧进行分析"""

    def __init__(self):
        self._yolo_model = None
        self._yolo_loaded = False

    def _load_yolo(self):
        if self._yolo_loaded:
            return
        try:
            from ultralytics import YOLO
            self._yolo_model = YOLO(YOLO_CONFIG["model"])
            self._yolo_loaded = True
            log.info("YOLO模型已加载")
        except Exception as e:
            log.warning(f"YOLO加载失败: {e}")

    def sample_frames(self, video_path: str, num_samples: int = 15) -> list[tuple[int, np.ndarray]]:
        """从视频中均匀采样帧"""
        info = get_video_info(video_path)
        if info is None or info.total_frames == 0:
            return []

        interval = max(1, info.total_frames // num_samples)
        cap = cv2.VideoCapture(video_path)
        frames = []

        for i in range(num_samples):
            frame_idx = i * interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frames.append((frame_idx, frame))

        cap.release()
        return frames

    def detect_objects(self, frame: np.ndarray) -> list[dict]:
        """检测画面中的物体/人脸"""
        self._load_yolo()
        if self._yolo_model is None:
            return []

        results = self._yolo_model(frame, verbose=False)
        detections = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = r.names[cls_id]
                conf = float(box.conf[0])
                if conf >= YOLO_CONFIG["conf_threshold"]:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections.append({
                        "class": cls_name,
                        "confidence": round(conf, 3),
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    })

        return detections

    def analyze_scene(self, frame: np.ndarray) -> dict:
        """
        分析单帧场景内容
        返回:
        {
            "has_face": bool,
            "has_text": bool,
            "has_product": bool,
            "main_subject": str,
            "face_region": [x, y, w, h] or None,
            "safe_regions": [[x, y, w, h]],  # 可以模糊处理的区域
            "critical_regions": [[x, y, w, h]],  # 不能处理的区域(人脸/文字)
        }
        """
        detections = self.detect_objects(frame)
        h, w = frame.shape[:2]

        result = {
            "has_face": False,
            "has_text": False,
            "has_product": False,
            "main_subject": "unknown",
            "face_region": None,
            "safe_regions": [],
            "critical_regions": [],
        }

        for det in detections:
            cls = det["class"]
            bbox = det["bbox"]
            x1, y1, x2, y2 = bbox

            if cls == "person":
                result["has_face"] = True
                # 人脸区域扩展
                face_h = y2 - y1
                result["face_region"] = [x1, max(0, y1 - int(face_h * 0.2)), x2, y2]
                result["critical_regions"].append(result["face_region"])
                result["main_subject"] = "person"
            elif cls in ("cell phone", "laptop", "tv", "book"):
                result["has_product"] = True
                result["critical_regions"].append(bbox)
            elif cls in ("bottle", "cup", "handbag", "sports ball"):
                result["has_product"] = True

        # 安全区域 = 画面四边 + 非关键区域
        margin = int(w * 0.1)
        result["safe_regions"] = [
            [0, 0, w, margin],           # 顶部
            [0, h - margin, w, margin],  # 底部
            [0, 0, margin, h],           # 左侧
            [w - margin, 0, margin, h],  # 右侧
        ]

        return result

    def analyze_video(self, video_path: str) -> dict:
        """
        分析完整视频，返回去重建议
        """
        frames = self.sample_frames(video_path)
        if not frames:
            return {"error": "无法采样视频帧"}

        analysis = {
            "scene_type": "未知",
            "has_face": False,
            "face_frequent": False,
            "has_text_overlay": False,
            "scene_changes": 0,
            "motion_level": "low",
            "suggested_mirror": True,
            "suggested_crop": 0.03,
            "suggested_speed": 1.03,
            "suggestions": [],
        }

        face_count = 0
        prev_frame = None

        for idx, (frame_idx, frame) in enumerate(frames):
            scene = self.analyze_scene(frame)

            if scene["has_face"]:
                face_count += 1

            # 检测场景切换（帧差异）
            if prev_frame is not None:
                diff = cv2.absdiff(frame, prev_frame)
                mean_diff = np.mean(diff)
                if mean_diff > 30:
                    analysis["scene_changes"] += 1

            prev_frame = frame.copy()

        # 统计分析
        face_ratio = face_count / len(frames)
        analysis["has_face"] = face_count > 0
        analysis["face_frequent"] = face_ratio > 0.5

        if face_count > len(frames) * 0.7:
            analysis["scene_type"] = "口播/出镜"
            analysis["suggested_mirror"] = False  # 口播不建议镜像
            analysis["suggested_crop"] = 0.02
            analysis["suggestions"].append("检测到大量人脸，禁用镜像翻转")
            analysis["suggestions"].append("在画面边缘轻微模糊，保留人脸清晰")
        elif analysis["scene_changes"] > len(frames) * 0.3:
            analysis["scene_type"] = "混剪/快节奏"
            analysis["suggested_speed"] = 1.02
            analysis["suggestions"].append("快节奏内容，减少变速幅度")
        else:
            analysis["scene_type"] = "产品展示/静止"
            analysis["suggested_crop"] = 0.04
            analysis["suggestions"].append("静止画面较多，可增强去重强度")

        return analysis


scene_analyzer = SceneAnalyzer()
