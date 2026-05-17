"""帧处理 - 基于 OpenCV 的逐帧操作"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from config.settings import log, TEMP_DIR


def extract_frames(
    video_path: str,
    output_dir: str = None,
    start_frame: int = 0,
    num_frames: int = None,
) -> list[str]:
    """从视频提取帧，返回帧文件路径列表"""
    output_dir = output_dir or str(TEMP_DIR / "frames")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if start_frame > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    frame_paths = []
    idx = start_frame
    max_idx = total if num_frames is None else start_frame + num_frames

    while idx < max_idx:
        ret, frame = cap.read()
        if not ret:
            break
        path = f"{output_dir}/frame_{idx:06d}.png"
        cv2.imwrite(path, frame)
        frame_paths.append(path)
        idx += 1

    cap.release()
    return frame_paths


def crop_frame(frame: np.ndarray, crop_percent: float) -> np.ndarray:
    """裁剪画面边缘（百分比）"""
    h, w = frame.shape[:2]
    dh = int(h * crop_percent)
    dw = int(w * crop_percent)
    return frame[dh:h - dh, dw:w - dw]


def scale_frame(frame: np.ndarray, scale: float) -> np.ndarray:
    """缩放画面"""
    h, w = frame.shape[:2]
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)


def rotate_frame(frame: np.ndarray, angle: float) -> np.ndarray:
    """旋转画面（小角度）"""
    h, w = frame.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(frame, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)


def mirror_frame(frame: np.ndarray) -> np.ndarray:
    """水平镜像翻转"""
    return cv2.flip(frame, 1)


def blur_region(frame: np.ndarray, x: int, y: int, w: int, h: int, kernel_size: int = 15) -> np.ndarray:
    """局部高斯模糊"""
    roi = frame[y:y + h, x:x + w]
    blurred = cv2.GaussianBlur(roi, (kernel_size, kernel_size), 0)
    frame[y:y + h, x:x + w] = blurred
    return frame


def blur_edges(frame: np.ndarray, edge_width: int = 10) -> np.ndarray:
    """模糊画面四边（毛玻璃边框效果）"""
    h, w = frame.shape[:2]
    # 上下左右四边
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(mask, (0, 0), (w, h), 255, -1)
    cv2.rectangle(mask, (edge_width, edge_width), (w - edge_width, h - edge_width), 0, -1)
    blurred = cv2.GaussianBlur(frame, (21, 21), 0)
    mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
    return (frame * (1 - mask_3ch) + blurred * mask_3ch).astype(np.uint8)


def adjust_brightness_contrast(frame: np.ndarray, alpha: float = 1.0, beta: float = 0.0) -> np.ndarray:
    """调整亮度和对比度，alpha=对比度倍数，beta=亮度增量"""
    return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)


def adjust_saturation(frame: np.ndarray, factor: float) -> np.ndarray:
    """调整饱和度，factor=1.0为不变"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
    hsv = hsv.astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def add_noise(frame: np.ndarray, intensity: float = 5.0) -> np.ndarray:
    """添加随机噪点"""
    noise = np.random.normal(0, intensity, frame.shape).astype(np.int16)
    result = frame.astype(np.int16) + noise
    return np.clip(result, 0, 255).astype(np.uint8)


def add_dynamic_border(
    frame: np.ndarray,
    border_width: int = 8,
    color: tuple = (255, 255, 255),
    frame_idx: int = 0,
) -> np.ndarray:
    """添加动态边框（颜色随帧变化）"""
    h, w = frame.shape[:2]
    # 颜色微调产生动态效果
    r, g, b = color
    offset = int(20 * np.sin(frame_idx * 0.1))
    r = np.clip(r + offset, 0, 255)
    g = np.clip(g + offset, 0, 255)
    b = np.clip(b + offset, 0, 255)
    return cv2.copyMakeBorder(frame, border_width, border_width, border_width, border_width,
                               cv2.BORDER_CONSTANT, value=(b, g, r))


def apply_lut(frame: np.ndarray, lut_matrix: np.ndarray) -> np.ndarray:
    """应用LUT色彩查找表"""
    return cv2.LUT(frame, lut_matrix)


def get_frame_count(video_path: str) -> int:
    """获取视频总帧数"""
    cap = cv2.VideoCapture(video_path)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return count


def get_frame_at(video_path: str, frame_idx: int) -> Optional[np.ndarray]:
    """获取指定索引的帧"""
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None
