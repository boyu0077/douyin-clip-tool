"""时间轴视图 - 多轨道剪辑时间轴"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QPushButton, QLabel, QSlider,
)
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QFont, QMouseEvent,
    QWheelEvent, QLinearGradient,
)
from core.timeline_model import TimelineModel
from core.track import Track, TrackType
from core.clip import Clip


class TimelineView(QWidget):
    """时间轴主视图"""

    clip_selected = pyqtSignal(str)          # clip_id
    clip_moved = pyqtSignal(str, float)      # clip_id, new_start
    playhead_moved = pyqtSignal(float)       # time_sec
    split_requested = pyqtSignal(str, float) # clip_id, split_time

    TRACK_HEIGHT = 55
    TRACK_HEADER_WIDTH = 80
    RULER_HEIGHT = 25

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self._timeline: TimelineModel = None
        self._playhead_pos = 0.0        # 秒
        self._zoom = 100                # 像素/秒
        self._scroll_x = 0
        self._selected_clip: str = None
        self._dragging_clip: str = None
        self._drag_start_pos = QPoint()
        self._drag_clip_orig_start = 0.0
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_timeline(self, timeline: TimelineModel):
        self._timeline = timeline
        self.update()

    @property
    def playhead_pos(self) -> float:
        return self._playhead_pos

    def set_playhead(self, time_sec: float):
        self._playhead_pos = max(0, time_sec)
        self.update()

    def set_zoom(self, zoom: int):
        self._zoom = max(10, min(500, zoom))
        self.update()

    # ========== 绘制 ==========

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # 背景
        painter.fillRect(0, 0, w, h, QColor("#1a1a2e"))

        if self._timeline is None:
            painter.setPen(QColor("#666"))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "请先导入素材")
            painter.end()
            return

        # 时间标尺
        self._draw_ruler(painter, w)

        # 轨道
        tracks = self._timeline.tracks
        y_offset = self.RULER_HEIGHT
        for i, track in enumerate(tracks):
            if track.visible:
                self._draw_track(painter, track, i, y_offset, w)
                y_offset += self.TRACK_HEIGHT

        # 播放头
        px = self._time_to_x(self._playhead_pos)
        painter.setPen(QPen(QColor("#e94560"), 2))
        painter.drawLine(px, 0, px, y_offset)

        painter.end()

    def _draw_ruler(self, painter: QPainter, width: int):
        painter.fillRect(0, 0, width, self.RULER_HEIGHT, QColor("#16213e"))
        painter.setPen(QPen(QColor("#0f3460"), 1))
        painter.drawLine(0, self.RULER_HEIGHT, width, self.RULER_HEIGHT)

        painter.setPen(QColor("#999"))
        font = QFont("Monospace", 9)
        painter.setFont(font)

        # 每秒钟一个刻度
        total_sec = int(self._width_to_time(width))

        for sec in range(0, total_sec + 1):
            x = self._time_to_x(sec) - self._scroll_x
            if x < 0 or x > width:
                continue

            is_major = sec % 5 == 0
            tick_h = 10 if is_major else 5
            painter.drawLine(int(x), self.RULER_HEIGHT - tick_h, int(x), self.RULER_HEIGHT)

            if is_major:
                m, s = divmod(sec, 60)
                text = f"{m}:{s:02d}"
                painter.drawText(int(x) + 3, 14, text)

    def _draw_track(self, painter: QPainter, track: Track, index: int,
                    y: int, width: int):
        # 轨道背景
        track_colors = {
            TrackType.VIDEO: QColor("#1a2a1a"),
            TrackType.AUDIO: QColor("#1a1a2a"),
            TrackType.SUBTITLE: QColor("#2a1a1a"),
            TrackType.EFFECT: QColor("#1a1a3a"),
        }
        bg = track_colors.get(track.track_type, QColor("#1a1a2e"))
        painter.fillRect(self.TRACK_HEADER_WIDTH, y, width - self.TRACK_HEADER_WIDTH, self.TRACK_HEIGHT, bg)

        # 轨道路径
        painter.fillRect(0, y, self.TRACK_HEADER_WIDTH, self.TRACK_HEIGHT, QColor("#0f3460"))
        painter.setPen(QColor("#c0c0c0"))
        painter.drawText(5, y + 18, track.name)

        # 轨道线
        painter.setPen(QPen(QColor("#0f3460"), 1))
        painter.drawLine(0, y + self.TRACK_HEIGHT, width, y + self.TRACK_HEIGHT)

        # 绘制片段
        for clip in track.clips:
            self._draw_clip(painter, clip, y, width, track.track_type)

    def _draw_clip(self, painter: QPainter, clip: Clip, y: int,
                   width: int, track_type: TrackType):
        x1 = self._time_to_x(clip.timeline_start)
        x2 = self._time_to_x(clip.end_time)
        clip_w = x2 - x1

        if x2 < 0 or x1 > width:
            return

        rect = QRect(int(x1) + self.TRACK_HEADER_WIDTH, y + 2,
                     max(4, int(clip_w)), self.TRACK_HEIGHT - 4)

        # 片段颜色
        colors = {
            TrackType.VIDEO: (QColor("#e94560"), QColor("#c03950")),
            TrackType.AUDIO: (QColor("#3498db"), QColor("#2980b9")),
            TrackType.SUBTITLE: (QColor("#2ecc71"), QColor("#27ae60")),
            TrackType.EFFECT: (QColor("#9b59b6"), QColor("#8e44ad")),
        }
        color1, color2 = colors.get(track_type, (QColor("#95a5a6"), QColor("#7f8c8d")))

        gradient = QLinearGradient(0, y, 0, y + self.TRACK_HEIGHT)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
        painter.fillRect(rect, gradient)

        # 选中状态
        if clip.id == self._selected_clip:
            painter.setPen(QPen(QColor("#fff"), 2, Qt.PenStyle.DashLine))
        else:
            painter.setPen(QPen(color2.darker(120), 1))
        painter.drawRect(rect)

        # 标签
        if rect.width() > 40:
            painter.setPen(QColor("#fff"))
            label = clip.label or f"{clip.duration:.1f}s"
            painter.drawText(rect.adjusted(4, 0, -4, -4),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                           label)

    # ========== 坐标转换 ==========

    def _time_to_x(self, time_sec: float) -> int:
        return int(time_sec * self._zoom) - self._scroll_x

    def _x_to_time(self, x: int) -> float:
        return (x + self._scroll_x - self.TRACK_HEADER_WIDTH) / self._zoom

    def _width_to_time(self, width: int) -> float:
        return (width + self._scroll_x) / self._zoom

    # ========== 鼠标事件 ==========

    def mousePressEvent(self, event: QMouseEvent):
        x, y = event.position().x(), event.position().y()

        if y < self.RULER_HEIGHT:
            # 点击标尺，移动播放头
            t = self._x_to_time(int(x))
            self.set_playhead(t)
            self.playhead_moved.emit(t)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击了片段
            track_idx = (int(y) - self.RULER_HEIGHT) // self.TRACK_HEIGHT
            if 0 <= track_idx < len(self._timeline.tracks):
                track = self._timeline.tracks[track_idx]
                t = self._x_to_time(int(x))
                for clip in track.clips:
                    if clip.timeline_start <= t <= clip.end_time:
                        self._selected_clip = clip.id
                        self._dragging_clip = clip.id
                        self._drag_start_pos = event.position()
                        self._drag_clip_orig_start = clip.timeline_start
                        self.clip_selected.emit(clip.id)
                        self.update()
                        return

        self._selected_clip = None
        self._dragging_clip = None
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging_clip:
            dx = event.position().x() - self._drag_start_pos.x()
            dt = dx / self._zoom
            new_start = max(0, self._drag_clip_orig_start + dt)
            clip = self._timeline.get_clip(self._dragging_clip)
            if clip:
                clip.timeline_start = new_start
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging_clip:
            clip = self._timeline.get_clip(self._dragging_clip)
            if clip:
                self.clip_moved.emit(clip.id, clip.timeline_start)
        self._dragging_clip = None

    def wheelEvent(self, event: QWheelEvent):
        """滚轮缩放"""
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom = min(500, self._zoom + 10)
        else:
            self._zoom = max(10, self._zoom - 10)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete and self._selected_clip:
            self._timeline.remove_clip(self._selected_clip)
            self._selected_clip = None
            self.update()
        elif event.key() == Qt.Key.Key_S and self._selected_clip:
            self.split_requested.emit(self._selected_clip, self._playhead_pos)
