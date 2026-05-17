"""AI模型下载管理对话框"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QProgressBar,
    QLabel, QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from ai_engine.model_manager import model_manager, ModelInfo
from config.settings import log


class DownloadThread(QThread):
    """模型下载线程"""
    progress = pyqtSignal(int, str)

    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name

    def run(self):
        model_manager.download_model(
            self.model_name,
            progress_callback=lambda p, m: self.progress.emit(p, m)
        )


class ModelDownloadDialog(QDialog):
    """模型管理对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI模型管理")
        self.setMinimumSize(550, 400)
        self._download_thread = None
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.label_status = QLabel("检测模型中...")
        layout.addWidget(self.label_status)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["模型", "大小", "状态", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        self.label_progress = QLabel("")
        layout.addWidget(self.label_progress)

        btn_layout = QHBoxLayout()
        self.btn_download_all = QPushButton("一键下载全部AI模型")
        self.btn_download_all.setObjectName("primaryBtn")
        self.btn_download_all.clicked.connect(self._on_download_all)
        btn_layout.addWidget(self.btn_download_all)

        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def _refresh(self):
        models = list(model_manager._models.values())
        self.table.setRowCount(len(models))

        for i, model in enumerate(models):
            self.table.setItem(i, 0, QTableWidgetItem(model.display_name))
            self.table.setItem(i, 1, QTableWidgetItem(
                f"{model.size_gb:.1f}GB" if model.size_gb >= 1 else f"{int(model.size_gb * 1000)}MB"
            ))

            if model.installed:
                self.table.setItem(i, 2, QTableWidgetItem("已安装"))
            elif model.required:
                self.table.setItem(i, 2, QTableWidgetItem("内置"))
            else:
                self.table.setItem(i, 2, QTableWidgetItem("未下载"))

            btn = QPushButton("下载" if not model.installed else "已安装")
            btn.setEnabled(not model.installed and not model.required)
            if not model.installed and not model.required:
                btn.clicked.connect(lambda checked, n=model.name: self._download_model(n))
            self.table.setCellWidget(i, 3, btn)

        self.label_status.setText(model_manager.get_status_summary())

    def _download_model(self, name: str):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self._download_thread = DownloadThread(name)
        self._download_thread.progress.connect(self._on_progress)
        self._download_thread.finished.connect(self._on_finished)
        self._download_thread.start()

    def _on_download_all(self):
        reply = QMessageBox.question(
            self, "确认下载",
            "将下载所有未安装的AI模型（约7GB），确认继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for model in model_manager._models.values():
                if not model.installed and not model.required:
                    self._download_model(model.name)

    def _on_progress(self, percent: int, msg: str):
        self.progress_bar.setValue(percent)
        self.label_progress.setText(msg)

    def _on_finished(self):
        self.progress_bar.setVisible(False)
        self.label_progress.setText("下载完成")
        self._refresh()
