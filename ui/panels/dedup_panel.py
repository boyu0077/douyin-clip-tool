"""去重配置面板 - 10种模板可选"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QSlider, QCheckBox, QGroupBox,
    QSpinBox, QDoubleSpinBox, QLineEdit, QScrollArea,
    QProgressBar, QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from dedup.engine import DedupConfig
from dedup.batch.batch_processor import BatchProcessor, TaskStatus
from config.presets import DEDUP_TEMPLATES
from config.settings import log


class DedupPanel(QWidget):
    """去重控制面板 - 支持10种场景模板"""

    process_requested = pyqtSignal(list, str)  # files, intensity/template
    ai_analyze_requested = pyqtSignal(str)     # file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._batch = BatchProcessor()
        self._template_name = "Vlog去重"
        self._config = DedupConfig.from_template(self._template_name)
        self._target_files: list[str] = []
        self._build_ui()
        self._connect_batch_signals()
        self._on_template_changed(self._template_name)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        header = QLabel("去重控制")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #e94560;")
        layout.addWidget(header)

        # 模板选择
        template_group = QGroupBox("去重模板")
        tlayout = QVBoxLayout(template_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("场景:"))
        self.combo_template = QComboBox()
        self.combo_template.addItems(list(DEDUP_TEMPLATES.keys()))
        self.combo_template.setCurrentText("Vlog去重")
        self.combo_template.currentTextChanged.connect(self._on_template_changed)
        row1.addWidget(self.combo_template)
        tlayout.addLayout(row1)

        self.label_desc = QLabel()
        self.label_desc.setWordWrap(True)
        self.label_desc.setStyleSheet("color: #aaa; font-size: 11px; padding: 2px;")
        tlayout.addWidget(self.label_desc)

        layout.addWidget(template_group)

        # 画面去重选项
        video_group = QGroupBox("画面处理")
        vlayout = QVBoxLayout(video_group)

        self.chk_mirror = QCheckBox("镜像翻转")
        vlayout.addWidget(self.chk_mirror)

        crop_layout = QHBoxLayout()
        crop_layout.addWidget(QLabel("裁剪比例:"))
        self.spin_crop = QDoubleSpinBox()
        self.spin_crop.setRange(0, 10)
        self.spin_crop.setSuffix("%")
        self.spin_crop.setSingleStep(0.5)
        crop_layout.addWidget(self.spin_crop)
        vlayout.addLayout(crop_layout)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("变速:"))
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(90, 110)
        self.spin_speed.setSuffix("%")
        self.spin_speed.setSingleStep(1)
        speed_layout.addWidget(self.spin_speed)
        vlayout.addLayout(speed_layout)

        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("抽帧(帧/秒):"))
        self.spin_drop = QSpinBox()
        self.spin_drop.setRange(0, 8)
        drop_layout.addWidget(self.spin_drop)
        vlayout.addLayout(drop_layout)

        layout.addWidget(video_group)

        # 色彩调整
        color_group = QGroupBox("色彩调整")
        clayout = QVBoxLayout(color_group)

        self._color_sliders = {}
        for label, attr in [("亮度", "brightness"), ("对比度", "contrast"), ("饱和度", "saturation")]:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label}:"))
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(-20, 20)
            slider.setValue(0)
            self._color_sliders[attr] = slider
            slider.valueChanged.connect(lambda v, a=attr: self._on_color_slider(a, v))
            row.addWidget(slider)
            clayout.addLayout(row)

        layout.addWidget(color_group)

        # 特效
        effect_group = QGroupBox("特效")
        elayout = QVBoxLayout(effect_group)
        self.chk_border = QCheckBox("动态边框")
        self.chk_shake = QCheckBox("画面微抖")
        self.chk_noise = QCheckBox("随机噪点")
        self.chk_blur = QCheckBox("边缘模糊")
        elayout.addWidget(self.chk_border)
        elayout.addWidget(self.chk_shake)
        elayout.addWidget(self.chk_noise)
        elayout.addWidget(self.chk_blur)
        layout.addWidget(effect_group)

        # 水印
        water_group = QGroupBox("水印")
        wlayout = QVBoxLayout(water_group)
        self.chk_watermark = QCheckBox("添加水印")
        self.edit_watermark = QLineEdit()
        self.edit_watermark.setPlaceholderText("输入水印文字...")
        wlayout.addWidget(self.chk_watermark)
        wlayout.addWidget(self.edit_watermark)
        layout.addWidget(water_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.btn_dedup = QPushButton("开始去重")
        self.btn_dedup.setObjectName("primaryBtn")
        self.btn_dedup.clicked.connect(self._on_start_dedup)
        btn_layout.addWidget(self.btn_dedup)

        self.btn_ai_analyze = QPushButton("AI分析")
        self.btn_ai_analyze.clicked.connect(self._on_ai_analyze)
        btn_layout.addWidget(self.btn_ai_analyze)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _on_template_changed(self, name: str):
        """切换模板时同步所有控件"""
        preset = DEDUP_TEMPLATES.get(name)
        if preset is None:
            return

        self._template_name = name
        self._config = DedupConfig.from_template(name)

        # 描述
        self.label_desc.setText(preset.description)

        # 画面
        self.chk_mirror.setChecked(preset.mirror)
        self.spin_crop.setValue(preset.crop_percent * 100)
        self.spin_speed.setValue(int((1.0 + preset.speed_change) * 100))
        self.spin_drop.setValue(preset.drop_frames)

        # 色彩滑块（取范围中间值）
        self._sync_color_sliders(preset)

        # 特效
        self.chk_border.setChecked(preset.border_enabled)
        self.chk_shake.setChecked(preset.shake_enabled)
        self.chk_noise.setChecked(preset.filter_enabled)
        self.chk_blur.setChecked(preset.blur_edges)

        # 水印
        self.chk_watermark.setChecked(preset.watermark_enabled)

    def _sync_color_sliders(self, preset):
        """将模板的色彩范围中间值同步到滑块"""
        for attr, rng in [
            ("brightness", preset.brightness_range),
            ("contrast", preset.contrast_range),
            ("saturation", preset.saturation_range),
        ]:
            mid = (rng[0] + rng[1]) / 2
            slider_val = int(mid * 100)
            # 对比度和饱和度以1.0为基准
            slider = self._color_sliders.get(attr)
            if slider:
                slider.blockSignals(True)
                slider.setValue(max(-20, min(20, slider_val)))
                slider.blockSignals(False)

    def _on_color_slider(self, attr: str, value: int):
        """色彩滑块变化时更新配置"""
        val = value / 100.0
        if attr == "brightness":
            self._config.brightness = val
        elif attr == "contrast":
            self._config.contrast = 1.0 + val
        elif attr == "saturation":
            self._config.saturation = 1.0 + val

    def _collect_config(self):
        """从UI控件收集当前配置"""
        self._config.mirror = self.chk_mirror.isChecked()
        self._config.crop_percent = self.spin_crop.value() / 100.0
        self._config.speed_factor = self.spin_speed.value() / 100.0
        self._config.drop_frames = self.spin_drop.value()
        self._config.dynamic_border = self.chk_border.isChecked()
        self._config.shake = self.chk_shake.isChecked()
        self._config.noise = self.chk_noise.isChecked()
        self._config.blur_edges = self.chk_blur.isChecked()
        self._config.watermark_enabled = self.chk_watermark.isChecked()
        self._config.watermark_text = self.edit_watermark.text()
        return self._config

    def _on_start_dedup(self):
        self._collect_config()
        self.process_requested.emit(self._target_files, self._template_name)

    def _on_ai_analyze(self):
        self.ai_analyze_requested.emit("")

    def _connect_batch_signals(self):
        self._batch.on_task_progress = self._on_batch_progress

    def _on_batch_progress(self, task_id: int, percent: int, msg: str):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(percent)

    def set_batch_targets(self, files: list[str]):
        """设置批量处理目标文件"""
        self._target_files = files

    @property
    def current_template(self) -> str:
        return self._template_name

    @property
    def current_config(self) -> DedupConfig:
        self._collect_config()
        return self._config
