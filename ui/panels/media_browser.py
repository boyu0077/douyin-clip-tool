"""素材浏览器面板"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QDrag
from config.settings import log


class MediaBrowserPanel(QWidget):
    """素材浏览器 - 导入、预览、拖入时间轴"""

    media_added = pyqtSignal(list)  # 发送文件路径列表
    media_selected = pyqtSignal(str)  # 发送选中文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self._media_files: list[str] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # 标题
        header = QLabel("素材浏览器")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #e94560;")
        layout.addWidget(header)

        # 导入按钮
        btn_layout = QHBoxLayout()
        self.btn_import = QPushButton("+ 导入视频")
        self.btn_import.setObjectName("primaryBtn")
        self.btn_import.clicked.connect(self._on_import)
        btn_layout.addWidget(self.btn_import)

        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self._on_clear)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        # 素材列表
        self.list_widget = QListWidget()
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)

    def add_files(self, filepaths: list[str]):
        added = []
        for fp in filepaths:
            if fp not in self._media_files:
                self._media_files.append(fp)
                item = QListWidgetItem(os.path.basename(fp))
                item.setToolTip(fp)
                item.setData(Qt.ItemDataRole.UserRole, fp)
                self.list_widget.addItem(item)
                added.append(fp)

        if added:
            log.info(f"已添加 {len(added)} 个素材")
            self.media_added.emit(added)

    def clear(self):
        self._media_files.clear()
        self.list_widget.clear()

    @property
    def files(self) -> list[str]:
        return self._media_files

    @property
    def count(self) -> int:
        return len(self._media_files)

    def _on_import(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "导入素材", "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.flv *.ts *.webm);;所有文件 (*)"
        )
        if files:
            self.add_files(files)

    def _on_clear(self):
        self.clear()

    def _on_item_clicked(self, item: QListWidgetItem):
        fp = item.data(Qt.ItemDataRole.UserRole)
        if fp:
            self.media_selected.emit(fp)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        fp = item.data(Qt.ItemDataRole.UserRole)
        if fp:
            self.media_selected.emit(fp)
