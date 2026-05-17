"""导出设置面板"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QSpinBox, QLineEdit,
    QProgressBar, QGroupBox, QFileDialog,
)
from PyQt6.QtCore import pyqtSignal
from config.presets import EXPORT_PRESETS
from config.settings import OUTPUT_DIR


class ExportPanel(QWidget):
    """导出面板"""

    export_requested = pyqtSignal(dict)  # 导出参数字典

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        header = QLabel("导出设置")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #e94560;")
        layout.addWidget(header)

        # 格式预设
        preset_group = QGroupBox("输出格式")
        playout = QVBoxLayout(preset_group)
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(list(EXPORT_PRESETS.keys()))
        self.combo_preset.setCurrentText("抖音竖屏1080P")
        playout.addWidget(QLabel("预设:"))
        playout.addWidget(self.combo_preset)
        layout.addWidget(preset_group)

        # 自定义参数
        custom_group = QGroupBox("自定义参数")
        clayout = QVBoxLayout(custom_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("宽度:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(360, 4096)
        self.spin_width.setValue(1080)
        row1.addWidget(self.spin_width)
        row1.addWidget(QLabel("高度:"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(360, 4096)
        self.spin_height.setValue(1920)
        row1.addWidget(self.spin_height)
        clayout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("帧率:"))
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(15, 60)
        self.spin_fps.setValue(30)
        row2.addWidget(self.spin_fps)
        row2.addWidget(QLabel("码率:"))
        self.edit_bitrate = QLineEdit("10M")
        self.edit_bitrate.setFixedWidth(70)
        row2.addWidget(self.edit_bitrate)
        clayout.addLayout(row2)

        layout.addWidget(custom_group)

        # 字幕烧录
        sub_group = QGroupBox("字幕")
        slayout = QHBoxLayout(sub_group)
        self.btn_select_srt = QPushButton("选择SRT字幕文件")
        self.btn_select_srt.clicked.connect(self._on_select_srt)
        self._srt_path = ""
        slayout.addWidget(self.btn_select_srt)
        layout.addWidget(sub_group)

        # 输出路径
        out_group = QGroupBox("输出")
        olayout = QHBoxLayout(out_group)
        self.edit_output = QLineEdit(str(OUTPUT_DIR))
        self.btn_browse = QPushButton("浏览")
        self.btn_browse.clicked.connect(self._on_browse_output)
        olayout.addWidget(self.edit_output)
        olayout.addWidget(self.btn_browse)
        layout.addWidget(out_group)

        # 进度
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 导出按钮
        self.btn_export = QPushButton("导出视频")
        self.btn_export.setObjectName("primaryBtn")
        self.btn_export.clicked.connect(self._on_export)
        layout.addWidget(self.btn_export)

        layout.addStretch()

    def _on_select_srt(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择字幕文件", "", "SRT字幕 (*.srt);;所有文件 (*)"
        )
        if path:
            self._srt_path = path

    def _on_browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.edit_output.setText(path)

    def _on_export(self):
        params = {
            "preset": self.combo_preset.currentText(),
            "width": self.spin_width.value(),
            "height": self.spin_height.value(),
            "fps": self.spin_fps.value(),
            "bitrate": self.edit_bitrate.text(),
            "output_dir": self.edit_output.text(),
            "srt_path": self._srt_path,
        }
        self.export_requested.emit(params)
