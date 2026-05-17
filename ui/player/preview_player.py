"""视频预览播放器 - 基于 QMediaPlayer"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QStyle, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class PreviewPlayer(QWidget):
    """视频预览播放器组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file = ""
        self._duration_ms = 0
        self._is_seeking = False
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 视频显示区域
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setStyleSheet("background-color: #000;")
        layout.addWidget(self.video_widget, 1)

        # 媒体播放器
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # 控制栏
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setContentsMargins(8, 4, 8, 4)
        ctrl_layout.setSpacing(8)

        # 播放/暂停
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(36, 36)
        self.btn_play.setObjectName("primaryBtn")
        ctrl_layout.addWidget(self.btn_play)

        # 逐帧后退
        self.btn_prev_frame = QPushButton("◀◀")
        self.btn_prev_frame.setFixedSize(36, 36)
        self.btn_prev_frame.setToolTip("后退1帧")
        ctrl_layout.addWidget(self.btn_prev_frame)

        # 逐帧前进
        self.btn_next_frame = QPushButton("▶▶")
        self.btn_next_frame.setFixedSize(36, 36)
        self.btn_next_frame.setToolTip("前进1帧")
        ctrl_layout.addWidget(self.btn_next_frame)

        # 时间显示
        self.label_time = QLabel("00:00 / 00:00")
        self.label_time.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        self.label_time.setMinimumWidth(120)
        ctrl_layout.addWidget(self.label_time)

        # 进度条
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ctrl_layout.addWidget(self.progress_slider, 1)

        # 音量控制
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(80)
        ctrl_layout.addWidget(self.volume_slider)

        layout.addLayout(ctrl_layout)

    def _connect_signals(self):
        self.btn_play.clicked.connect(self.toggle_play)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.playbackStateChanged.connect(self._on_state_changed)
        self.btn_prev_frame.clicked.connect(lambda: self.step_frame(-1))
        self.btn_next_frame.clicked.connect(lambda: self.step_frame(1))

    def load(self, filepath: str):
        """加载视频文件"""
        self._current_file = filepath
        self.media_player.setSource(QUrl.fromLocalFile(filepath))
        self.label_time.setText("00:00 / 00:00")
        self.btn_play.setText("▶")

    def play(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def step_frame(self, direction: int = 1):
        """逐帧步进（方向：1前进，-1后退）"""
        fps = 30
        frame_ms = int(1000 / fps)
        pos = self.media_player.position() + direction * frame_ms
        pos = max(0, min(pos, self._duration_ms))
        self.media_player.setPosition(pos)

    def seek(self, position_ms: int):
        """跳转到指定位置（毫秒）"""
        self.media_player.setPosition(position_ms)

    def seek_ratio(self, ratio: float):
        """按比例跳转"""
        self.media_player.setPosition(int(self._duration_ms * ratio))

    def set_volume(self, volume: int):
        """设置音量 0-100"""
        self.audio_output.setVolume(volume / 100.0)

    @property
    def current_position_ms(self) -> int:
        return self.media_player.position()

    @property
    def duration_ms(self) -> int:
        return self._duration_ms

    @property
    def is_playing(self) -> bool:
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    # ===== 事件处理 =====

    def _on_slider_pressed(self):
        self._is_seeking = True
        self.pause()

    def _on_slider_released(self):
        ratio = self.progress_slider.value() / 1000.0
        self.seek_ratio(ratio)
        self._is_seeking = False

    def _on_volume_changed(self, value: int):
        self.set_volume(value)

    def _on_duration_changed(self, duration_ms: int):
        self._duration_ms = duration_ms
        self._update_time_label()

    def _on_position_changed(self, position_ms: int):
        if not self._is_seeking and self._duration_ms > 0:
            self.progress_slider.setValue(int(position_ms / self._duration_ms * 1000))
        self._update_time_label()

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setText("⏸")
        else:
            self.btn_play.setText("▶")

    def _update_time_label(self):
        pos = self.media_player.position()
        dur = self._duration_ms
        self.label_time.setText(
            f"{self._ms_to_str(pos)} / {self._ms_to_str(dur)}"
        )

    @staticmethod
    def _ms_to_str(ms: int) -> str:
        s = ms // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
