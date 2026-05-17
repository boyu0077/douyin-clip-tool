"""属性面板 - 显示和编辑选中片段的属性"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox,
    QDoubleSpinBox, QSpinBox, QComboBox,
    QPushButton, QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal


class PropertyPanel(QWidget):
    """选中片段属性编辑器"""

    value_changed = pyqtSignal(str, str, object)  # clip_id, property, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_clip = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("属性面板")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #e94560;")
        layout.addWidget(header)

        # 片段信息
        self.group_clip = QGroupBox("片段信息")
        glayout = QVBoxLayout(self.group_clip)
        self.label_info = QLabel("未选中片段")
        glayout.addWidget(self.label_info)
        layout.addWidget(self.group_clip)

        # 速度
        speed_group = QGroupBox("播放设置")
        s_layout = QVBoxLayout(speed_group)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("速度:"))
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(0.5, 2.0)
        self.spin_speed.setSingleStep(0.05)
        self.spin_speed.setValue(1.0)
        self.spin_speed.valueChanged.connect(lambda v: self._emit_change("speed", v))
        row1.addWidget(self.spin_speed)
        s_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("音量:"))
        self.spin_volume = QDoubleSpinBox()
        self.spin_volume.setRange(0.0, 2.0)
        self.spin_volume.setSingleStep(0.1)
        self.spin_volume.setValue(1.0)
        self.spin_volume.valueChanged.connect(lambda v: self._emit_change("volume", v))
        row2.addWidget(self.spin_volume)
        s_layout.addLayout(row2)
        layout.addWidget(speed_group)

        # 去重强度（针对此片段）
        dedup_group = QGroupBox("去重强度")
        d_layout = QVBoxLayout(dedup_group)
        self.combo_dedup = QComboBox()
        self.combo_dedup.addItems(["跟随全局", "低", "中", "高"])
        d_layout.addWidget(self.combo_dedup)
        layout.addWidget(dedup_group)

        # 快捷操作
        action_group = QGroupBox("快捷操作")
        a_layout = QHBoxLayout(action_group)
        self.btn_split = QPushButton("切割")
        self.btn_split.clicked.connect(lambda: self._emit_action("split"))
        a_layout.addWidget(self.btn_split)
        self.btn_delete = QPushButton("删除")
        self.btn_delete.clicked.connect(lambda: self._emit_action("delete"))
        a_layout.addWidget(self.btn_delete)
        layout.addWidget(action_group)

        layout.addStretch()

    def set_clip(self, clip_data: dict = None):
        """更新片段属性显示"""
        self._current_clip = clip_data
        if clip_data:
            self.label_info.setText(
                f"源文件: {clip_data.get('label', 'N/A')}\n"
                f"时长: {clip_data.get('duration', 0):.1f}s\n"
                f"分辨率: {clip_data.get('resolution', 'N/A')}"
            )
            self.spin_speed.setValue(clip_data.get("speed", 1.0))
            self.spin_volume.setValue(clip_data.get("volume", 1.0))
        else:
            self.label_info.setText("未选中片段")

    def _emit_change(self, prop: str, value):
        if self._current_clip:
            self.value_changed.emit(self._current_clip.get("id", ""), prop, value)

    def _emit_action(self, action: str):
        if self._current_clip:
            self.value_changed.emit(self._current_clip.get("id", ""), "__action__", action)
