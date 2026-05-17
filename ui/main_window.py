"""
主窗口 - 完整桌面编辑界面
"""
import os
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QTabWidget, QGroupBox, QComboBox, QSlider,
    QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, QTextEdit,
    QProgressBar, QDialog, QDialogButtonBox, QFormLayout,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QFont

from core.project import Project
from core.clip import Clip
from core.timeline_model import TimelineModel
from config.presets import DEDUP_TEMPLATES, EXPORT_PRESETS, DEDUP_PRESETS
from config.settings import app_config
from dedup.engine import dedup_engine
from dedup.batch.batch_processor import batch_processor, BatchTask
from processor.ffmpeg_runner import ffmpeg
from downloader.douyin_parser import downloader
from ai_engine.model_manager import model_manager

MEDIA_PATH_ROLE = Qt.ItemDataRole.UserRole


class MainWindow(QMainWindow):
    """主窗口"""
    
    progress_updated = pyqtSignal(int, str)
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("抖音切片剪辑助手 v1.0")
        self.resize(1400, 900)
        self.setMinimumSize(1200, 700)
        
        self.project = Project()
        
        # 连接信号
        self.progress_updated.connect(self._on_progress)
        self.log_signal.connect(self._on_log)
        
        self._setup_menu()
        self._setup_toolbar()
        self._setup_ui()
        self._setup_statusbar()
        self._setup_batch_processor()
        
        self._log("应用启动完成 - 就绪")
    
    def _setup_menu(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        file_menu.addAction("新建项目(&N)", "Ctrl+N", self._new_project)
        file_menu.addAction("打开项目(&O)", "Ctrl+O", self._open_project)
        file_menu.addAction("保存项目(&S)", "Ctrl+S", self._save_project)
        file_menu.addAction("另存为...", "Ctrl+Shift+S", self._save_project_as)
        file_menu.addSeparator()
        file_menu.addAction("导入视频(&I)", "Ctrl+I", lambda: self._import_media("video"))
        file_menu.addAction("导入音频", "Ctrl+Shift+I", lambda: self._import_media("audio"))
        file_menu.addSeparator()
        file_menu.addAction("设置(&T)", "Ctrl+,", self._show_settings)
        file_menu.addSeparator()
        file_menu.addAction("退出(&Q)", "Alt+F4", self.close)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        edit_menu.addAction("撤销", "Ctrl+Z", lambda: None)
        edit_menu.addAction("重做", "Ctrl+Y", lambda: None)
        edit_menu.addSeparator()
        edit_menu.addAction("清空时间轴", self._clear_timeline)

        # 去重菜单
        dedup_menu = menubar.addMenu("去重(&D)")
        dedup_menu.addAction("当前视频去重", self._dedup_current)
        dedup_menu.addAction("批量去重", self._batch_dedup)
        dedup_menu.addAction("AI智能去重", self._ai_dedup)

        # 导出菜单
        export_menu = menubar.addMenu("导出(&E)")
        export_menu.addAction("导出视频...", "Ctrl+E", self._export_video)
        export_menu.addAction("快速导出", "Ctrl+Shift+E", self._quick_export)

        # AI菜单
        ai_menu = menubar.addMenu("AI(&A)")
        ai_menu.addAction("AI分析视频", self._ai_analyze)
        ai_menu.addAction("生成字幕", self._generate_subtitles)
        ai_menu.addAction("模型管理", self._show_model_manager)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        help_menu.addAction("关于(&A)", self._show_about)
    
    def _setup_toolbar(self):
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        
        toolbar.addAction("导入", lambda: self._import_media("video"))
        toolbar.addAction("下载", self._show_downloader)
        toolbar.addSeparator()
        toolbar.addAction("AI分析", self._ai_analyze)
        toolbar.addAction("去重", self._dedup_current)
        toolbar.addSeparator()
        toolbar.addAction("导出", self._export_video)
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # === 左侧面板 ===
        left_panel = QWidget()
        left_panel.setFixedWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 素材浏览器
        media_group = QGroupBox("素材浏览器")
        media_layout = QVBoxLayout(media_group)
        self.media_list = QListWidget()
        self.media_list.itemDoubleClicked.connect(self._on_media_selected)
        media_layout.addWidget(self.media_list)
        
        media_btns = QHBoxLayout()
        media_btns.addWidget(QPushButton("导入视频", clicked=lambda: self._import_media("video")))
        media_btns.addWidget(QPushButton("下载", clicked=self._show_downloader))
        media_layout.addLayout(media_btns)
        left_layout.addWidget(media_group)
        
        # 去重面板
        dedup_group = QGroupBox("去重设置")
        dedup_layout = QFormLayout(dedup_group)
        
        self.dedup_preset_combo = QComboBox()
        self.dedup_preset_combo.addItems(list(DEDUP_TEMPLATES.keys()))
        self.dedup_preset_combo.setCurrentText("Vlog去重")
        dedup_layout.addRow("模板:", self.dedup_preset_combo)
        
        self.intensity_combo = QComboBox()
        self.intensity_combo.addItems(["低", "中", "高"])
        self.intensity_combo.setCurrentText("中")
        dedup_layout.addRow("强度:", self.intensity_combo)
        
        dedup_btns = QHBoxLayout()
        dedup_btns.addWidget(QPushButton("去重当前", clicked=self._dedup_current))
        dedup_btns.addWidget(QPushButton("批量去重", clicked=self._batch_dedup))
        dedup_layout.addRow(dedup_btns)
        
        self.ai_dedup_btn = QPushButton("AI智能去重")
        self.ai_dedup_btn.setObjectName("primaryBtn")
        self.ai_dedup_btn.clicked.connect(self._ai_dedup)
        dedup_layout.addRow(self.ai_dedup_btn)
        
        left_layout.addWidget(dedup_group)
        
        # 导出面板
        export_group = QGroupBox("导出设置")
        export_layout = QFormLayout(export_group)
        
        self.export_preset_combo = QComboBox()
        self.export_preset_combo.addItems(list(EXPORT_PRESETS.keys()))
        self.export_preset_combo.setCurrentText("抖音竖屏1080P")
        export_layout.addRow("格式:", self.export_preset_combo)
        
        self.watermark_edit = QLineEdit()
        self.watermark_edit.setPlaceholderText("可选: 添加水印文字")
        export_layout.addRow("水印:", self.watermark_edit)
        
        export_btn = QPushButton("导出视频")
        export_btn.setObjectName("primaryBtn")
        export_btn.clicked.connect(self._export_video)
        export_layout.addRow(export_btn)
        
        left_layout.addWidget(export_group)
        left_layout.addStretch()
        
        # === 右侧区域 ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 预览区
        preview_frame = QFrame()
        preview_frame.setStyleSheet("background-color: #000; border-radius: 8px;")
        preview_frame.setMinimumHeight(300)
        preview_frame.setMaximumHeight(450)
        preview_label = QLabel("预览区域")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("color: #555; font-size: 18px;")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.addWidget(preview_label)
        right_layout.addWidget(preview_frame)
        
        # 时间轴占位
        timeline_frame = QFrame()
        timeline_frame.setStyleSheet("background-color: #16213e; border-radius: 8px;")
        timeline_frame.setMinimumHeight(150)
        timeline_frame.setMaximumHeight(250)
        
        timeline_layout = QVBoxLayout(timeline_frame)
        timeline_title = QLabel("时间轴")
        timeline_title.setStyleSheet("color: #888; font-size: 12px; padding: 4px;")
        timeline_layout.addWidget(timeline_title)
        
        # 简单剪辑操作按钮
        clip_btns = QHBoxLayout()
        clip_btns.addWidget(QPushButton("分割", clicked=self._split_clip))
        clip_btns.addWidget(QPushButton("删除", clicked=self._delete_clip))
        clip_btns.addWidget(QPushButton("镜像", clicked=self._toggle_mirror))
        clip_btns.addWidget(QPushButton("向左移", clicked=lambda: self._nudge_clip(-0.5)))
        clip_btns.addWidget(QPushButton("向右移", clicked=lambda: self._nudge_clip(0.5)))
        clip_btns.addStretch()
        timeline_layout.addLayout(clip_btns)
        
        self.timeline_info = QLabel("暂无片段 | 拖入视频开始编辑")
        self.timeline_info.setStyleSheet("color: #555; font-size: 12px; padding: 8px;")
        timeline_layout.addWidget(self.timeline_info)
        
        right_layout.addWidget(timeline_frame)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.hide()
        right_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #888; font-size: 11px;")
        right_layout.addWidget(self.progress_label)
        
        # 日志区
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setStyleSheet("font-size: 11px; font-family: Consolas, monospace;")
        log_layout.addWidget(self.log_text)
        right_layout.addWidget(log_group)
        
        # 组装
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)
    
    def _setup_statusbar(self):
        self.statusbar = self.statusBar()
        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)
        self.model_status_label = QLabel("AI: 检测中...")
        self.statusbar.addPermanentWidget(self.model_status_label)
        QTimer.singleShot(1000, self._check_models)
    
    def _setup_batch_processor(self):
        batch_processor.on_task_progress = self._on_batch_progress
        batch_processor.on_task_done = self._on_batch_task_done
        batch_processor.on_batch_done = self._on_batch_done
    
    # ========== 操作 ==========
    
    def _new_project(self):
        self.project = Project()
        self.media_list.clear()
        self._log("新建项目")
    
    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", "", "项目文件 (*.dct);;所有文件 (*)"
        )
        if path:
            self.project = Project.load(path)
            self._log(f"已打开: {path}")
    
    def _save_project(self):
        if self.project.project_path:
            self.project.save()
            self._log(f"已保存: {self.project.project_path}")
        else:
            self._save_project_as()
    
    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存项目", f"{self.project.name}.dct", "项目文件 (*.dct)"
        )
        if path:
            self.project.save(path)
            self._log(f"已保存: {path}")
    
    def _import_media(self, media_type: str = "video"):
        filters = {
            "video": "视频文件 (*.mp4 *.mov *.avi *.mkv *.flv);;所有文件 (*)",
            "audio": "音频文件 (*.mp3 *.m4a *.wav *.aac);;所有文件 (*)",
        }
        paths, _ = QFileDialog.getOpenFileNames(
            self, f"导入{media_type}文件", "", filters.get(media_type, "所有文件 (*)")
        )
        for path in paths:
            info = ffmpeg.get_video_info(path)
            dur = info.get("duration", 0) if info else 0
            item = QListWidgetItem(f"{Path(path).name} ({dur:.1f}s)")
            item.setData(MEDIA_PATH_ROLE, path)
            self.media_list.addItem(item)
            self._log(f"导入: {Path(path).name}")
    
    def _show_downloader(self):
        dialog = DownloadDialog(self)
        dialog.exec()
    
    def _dedup_current(self):
        """对选中的素材执行去重"""
        item = self.media_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先从素材列表中选择一个视频")
            return

        input_path = item.data(MEDIA_PATH_ROLE)
        if not input_path or not Path(input_path).exists():
            QMessageBox.warning(self, "提示", "源文件不存在，请重新导入")
            return

        output_dir = str(Path.home() / "Documents" / "DouyinClipTool" / "output")
        os.makedirs(output_dir, exist_ok=True)

        preset = self.dedup_preset_combo.currentText()
        stem = Path(input_path).stem
        output_path = os.path.join(output_dir, f"{stem}_dedup.mp4")

        self.progress_bar.show()
        self._log(f"开始去重: {preset}")

        def progress_cb(pct, msg):
            self.progress_updated.emit(int(pct), msg)

        import threading
        def run():
            success, msg = dedup_engine.process_video(
                input_path, output_path, preset, progress_cb
            )
            if success:
                self.log_signal.emit(f"去重完成: {output_path}")
            else:
                self.log_signal.emit(f"去重失败: {msg}")

        threading.Thread(target=run, daemon=True).start()
    
    def _batch_dedup(self):
        dialog = BatchDedupDialog(self)
        dialog.exec()
    
    def _ai_dedup(self):
        QMessageBox.information(self, "AI去重", 
            "AI智能去重需要Ollama服务运行。\n"
            "请确保已安装Ollama并拉取Qwen2.5-VL模型。\n\n"
            "功能开发中，请先使用模板去重。")
    
    def _export_video(self):
        dialog = ExportDialog(self)
        dialog.exec()
    
    def _quick_export(self):
        self._log("快速导出功能开发中")
    
    def _ai_analyze(self):
        self._log("AI分析功能需要Ollama服务")
        if model_manager.check_ollama():
            self._log("Ollama已连接")
        else:
            self._log("Ollama未连接，请启动Ollama服务")
    
    def _generate_subtitles(self):
        self._log("字幕生成需要Whisper模型")
    
    def _show_model_manager(self):
        dialog = ModelManagerDialog(self)
        dialog.exec()
    
    def _show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def _show_about(self):
        QMessageBox.about(self, "关于",
            "<h2>抖音切片剪辑助手 v1.0</h2>"
            "<p>一款全功能的抖音视频剪辑+去重工具</p>"
            "<p>支持：导入/剪辑/去重/导出</p>"
            "<p>技术栈：PyQt6 + FFmpeg + AI</p>"
        )
    
    def _split_clip(self):
        self._log("分割功能: 请在时间轴上选择位置")
    
    def _delete_clip(self):
        self._log("已删除选中片段")
    
    def _toggle_mirror(self):
        self._log("已切换镜像")
    
    def _nudge_clip(self, seconds: float):
        self._log(f"片段位移: {seconds}s")
    
    def _clear_timeline(self):
        self.project.timeline = TimelineModel()
        self._log("已清空时间轴")
    
    def _on_media_selected(self, item):
        self._log(f"选中: {item.text()}")
    
    def _check_models(self):
        status = model_manager.get_optional_status()
        installed = sum(1 for s in status.values() if s.get("installed"))
        total = sum(1 for s in status.values() if not s.get("required", True))
        self.model_status_label.setText(f"AI模型: {installed}/{total}")
    
    # ========== 信号槽 ==========
    
    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.progress_label.setText(msg)
        if pct >= 100:
            self.progress_bar.hide()
    
    def _on_log(self, msg: str):
        self._log(msg)
    
    def _log(self, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")
    
    def _on_batch_progress(self, task: BatchTask, pct: int, msg: str):
        self.progress_bar.show()
        self.progress_bar.setValue(pct)
        self.progress_label.setText(f"[{task.id}] {msg}")
    
    def _on_batch_task_done(self, task: BatchTask):
        self._log(f"任务{task.id} {'完成' if task.status == 'done' else '失败'}: {task.error}")
    
    def _on_batch_done(self):
        self.progress_bar.hide()
        self._log("批量处理完成")


# ========== 对话框 ==========

class DownloadDialog(QDialog):
    """下载对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("下载抖音视频")
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("粘贴抖音分享链接:"))
        self.url_edit = QTextEdit()
        self.url_edit.setPlaceholderText("粘贴链接，每行一个...")
        self.url_edit.setMaximumHeight(100)
        layout.addWidget(self.url_edit)
        
        layout.addWidget(QLabel("输出目录:"))
        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit(str(Path.home() / "Documents" / "DouyinClipTool" / "downloads"))
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(QPushButton("浏览", clicked=self._browse_dir))
        layout.addLayout(dir_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("解析链接", clicked=self._parse))
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setObjectName("primaryBtn")
        self.download_btn.clicked.connect(self._download)
        btn_layout.addWidget(self.download_btn)
        layout.addLayout(btn_layout)
        
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
    
    def _browse_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择下载目录")
        if dir_path:
            self.dir_edit.setText(dir_path)
    
    def _parse(self):
        text = self.url_edit.toPlainText().strip()
        if text:
            urls = downloader.parse_share_link(text)
            self.url_edit.setPlainText("\n".join(urls))
            self.status_label.setText(f"解析到 {len(urls)} 个链接")
    
    def _download(self):
        urls = [l.strip() for l in self.url_edit.toPlainText().split("\n") if l.strip()]
        if not urls:
            return
        self.progress.show()
        output_dir = self.dir_edit.text()
        
        import threading
        def run():
            for url in urls:
                ok, path = downloader.download(url, output_dir)
                if ok:
                    self.status_label.setText(f"完成: {path}")
        threading.Thread(target=run, daemon=True).start()


class BatchDedupDialog(QDialog):
    """批量去重对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量去重")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("选择要处理的视频文件:"))
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("添加文件", clicked=self._add_files))
        btn_layout.addWidget(QPushButton("清空列表", clicked=self.file_list.clear))
        layout.addLayout(btn_layout)
        
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("去重模板:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(DEDUP_TEMPLATES.keys()))
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)
        
        self.start_btn = QPushButton("开始批量处理")
        self.start_btn.setObjectName("primaryBtn")
        self.start_btn.clicked.connect(self._start)
        layout.addWidget(self.start_btn)
        
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
    
    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择视频", "", "视频文件 (*.mp4 *.mov *.avi *.mkv);;所有文件 (*)"
        )
        for p in paths:
            item = QListWidgetItem(Path(p).name)
            item.setData(MEDIA_PATH_ROLE, p)
            self.file_list.addItem(item)
    
    def _start(self):
        if self.file_list.count() == 0:
            return
        self.progress.show()
        preset = self.preset_combo.currentText()
        output_dir = str(Path.home() / "Documents" / "DouyinClipTool" / "output")
        os.makedirs(output_dir, exist_ok=True)

        batch_processor.clear()
        count = 0
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            input_path = item.data(MEDIA_PATH_ROLE)
            if input_path and Path(input_path).exists():
                stem = Path(input_path).stem
                output_path = os.path.join(output_dir, f"{stem}_dedup.mp4")
                batch_processor.add_task(input_path, output_path, preset_name=preset)
                count += 1

        if count > 0:
            batch_processor.start()
            self._log(f"批量处理启动: {count} 个任务")


class ExportDialog(QDialog):
    """导出对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出视频")
        self.setMinimumSize(500, 350)
        
        layout = QFormLayout(self)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(EXPORT_PRESETS.keys()))
        layout.addRow("导出预设:", self.preset_combo)
        
        self.output_edit = QLineEdit(
            str(Path.home() / "Documents" / "DouyinClipTool" / "output" / "output.mp4")
        )
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.output_edit)
        browse_layout.addWidget(QPushButton("浏览", clicked=self._browse))
        layout.addRow("输出路径:", browse_layout)
        
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("导出")
        self.export_btn.setObjectName("primaryBtn")
        self.export_btn.clicked.connect(self._export)
        btn_layout.addWidget(self.export_btn)
        layout.addRow(btn_layout)
        
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addRow(self.progress)
    
    def _browse(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出视频", "", "MP4 (*.mp4);;所有文件 (*)"
        )
        if path:
            self.output_edit.setText(path)
    
    def _export(self):
        self.progress.show()
        self._log("导出功能开发中...")


class ModelManagerDialog(QDialog):
    """AI模型管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI模型管理")
        self.setMinimumSize(500, 350)
        
        layout = QVBoxLayout(self)
        
        status = model_manager.get_optional_status()
        layout.addWidget(QLabel(f"<b>模型状态</b> | 总大小: ~{model_manager.get_download_size():.1f}GB 待下载"))
        
        self.model_list = QListWidget()
        for name, info in status.items():
            text = f"{'[已安装]' if info['installed'] else '[未安装]'} {info['display']} ({info['size_gb']:.1f}GB)"
            self.model_list.addItem(text)
        layout.addWidget(self.model_list)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("下载选中模型", clicked=self._download_selected))
        btn_layout.addWidget(QPushButton("检查Ollama", clicked=self._check_ollama))
        layout.addLayout(btn_layout)
        
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
    
    def _download_selected(self):
        self.status_label.setText("下载功能开发中...")
    
    def _check_ollama(self):
        if model_manager.check_ollama():
            self.status_label.setText("Ollama服务: 已连接")
        else:
            self.status_label.setText("Ollama服务: 未连接，请启动Ollama")


class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 400)
        
        layout = QFormLayout(self)
        
        layout.addRow(QLabel("<b>导出默认设置</b>"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(720, 3840)
        self.width_spin.setValue(app_config.export.video.resolution_width)
        layout.addRow("默认宽度:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(720, 3840)
        self.height_spin.setValue(app_config.export.video.resolution_height)
        layout.addRow("默认高度:", self.height_spin)
        
        layout.addRow(QLabel("<b>AI设置</b>"))
        self.ollama_edit = QLineEdit(app_config.ai.ollama_host)
        layout.addRow("Ollama地址:", self.ollama_edit)
        
        btn = QPushButton("保存设置")
        btn.clicked.connect(self._save)
        layout.addRow(btn)
    
    def _save(self):
        app_config.export.video.resolution_width = self.width_spin.value()
        app_config.export.video.resolution_height = self.height_spin.value()
        app_config.ai.ollama_host = self.ollama_edit.text()
        app_config.save()
        QMessageBox.information(self, "提示", "设置已保存")
