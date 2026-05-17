"""音频波形显示组件"""
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen


class WaveformWidget(QWidget):
    """音频波形可视化"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setMaximumHeight(120)
        self._samples = np.array([])
        self._play_position = 0.0
        self._duration = 0.0
        self._in_point = 0.0
        self._out_point = 1.0
        self.setMouseTracking(True)

    def load_waveform(self, audio_samples: np.ndarray, duration: float):
        """加载波形数据"""
        self._samples = audio_samples
        self._duration = duration
        self._play_position = 0
        self.update()

    def clear(self):
        self._samples = np.array([])
        self.update()

    def set_play_position(self, position_sec: float):
        self._play_position = position_sec
        self.update()

    def set_range(self, in_sec: float, out_sec: float):
        """设置入出点"""
        if self._duration > 0:
            self._in_point = in_sec / self._duration
            self._out_point = out_sec / self._duration
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        mid_y = h // 2

        # 背景
        painter.fillRect(0, 0, w, h, QColor("#16213e"))

        if len(self._samples) == 0:
            painter.setPen(QColor("#666"))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "无波形数据")
            painter.end()
            return

        # 计算显示范围
        in_x = int(self._in_point * w)
        out_x = int(self._out_point * w)

        # 非选区暗化
        if in_x > 0:
            painter.fillRect(0, 0, in_x, h, QColor(0, 0, 0, 100))
        if out_x < w:
            painter.fillRect(out_x, 0, w - out_x, h, QColor(0, 0, 0, 100))

        # 选区高亮
        painter.fillRect(in_x, 0, max(1, out_x - in_x), h, QColor(233, 69, 96, 30))

        # 波形绘制
        step = max(1, len(self._samples) // w)
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor("#e94560"))
        gradient.setColorAt(1, QColor("#0f3460"))
        pen = QPen(gradient, 1)

        for x in range(w):
            idx = int(x * step)
            if idx >= len(self._samples):
                break
            amp = abs(self._samples[idx])
            amp = min(1.0, amp) * (mid_y - 2)

            color = QColor("#e94560") if in_x <= x <= out_x else QColor("#555")
            pen.setColor(color)
            painter.setPen(pen)

            if amp > 0.5:
                painter.drawLine(x, int(mid_y - amp), x, int(mid_y + amp))

        # 播放位置线
        if self._duration > 0:
            pos_x = int(self._play_position / self._duration * w)
            painter.setPen(QPen(QColor("#fff"), 2))
            painter.drawLine(pos_x, 0, pos_x, h)

        painter.end()
