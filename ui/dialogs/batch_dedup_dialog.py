"""批量去重进度对话框"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QProgressBar,
    QLabel, QHeaderView,
)
from PyQt6.QtCore import Qt
from dedup.batch.batch_processor import BatchProcessor, DedupTask, TaskStatus


class BatchDedupDialog(QDialog):
    """批量去重进度对话框"""

    def __init__(self, processor: BatchProcessor, parent=None):
        super().__init__(parent)
        self._processor = processor
        self.setWindowTitle("批量去重处理")
        self.setMinimumSize(600, 400)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 总体进度
        self.label_progress = QLabel("准备中...")
        layout.addWidget(self.label_progress)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 任务列表
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["文件", "状态", "进度", "耗时"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        # 按钮
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始处理")
        self.btn_start.setObjectName("primaryBtn")
        self.btn_start.clicked.connect(self._on_start)
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        btn_layout.addWidget(self.btn_stop)

        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self._processor.on_task_progress = self._on_task_progress
        self._processor.on_task_status_change = self._on_status_change
        self._processor.on_all_complete = self._on_all_complete

    def refresh_table(self):
        tasks = self._processor.get_all_tasks()
        self.table.setRowCount(len(tasks))
        for i, task in enumerate(tasks):
            from pathlib import Path
            self.table.setItem(i, 0, QTableWidgetItem(Path(task.input_path).name))
            self.table.setItem(i, 1, QTableWidgetItem(task.status.value))
            self.table.setItem(i, 2, QTableWidgetItem(f"{task.progress}%"))
            self.table.setItem(i, 3, QTableWidgetItem(task.elapsed_str))

    def _on_task_progress(self, task_id: int, percent: int, msg: str):
        self.refresh_table()

    def _on_status_change(self, task_id: int, status: TaskStatus):
        self.refresh_table()
        total = self._processor.total_count
        completed = self._processor.completed_count
        self.progress_bar.setValue(int(completed / total * 100) if total else 0)
        self.label_progress.setText(f"已完成: {completed}/{total}")

    def _on_all_complete(self, completed: int, total: int):
        self.progress_bar.setValue(100)
        self.label_progress.setText(f"全部完成! {completed}/{total}")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(False)

    def _on_start(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._processor.start()

    def _on_stop(self):
        self._processor.stop()
        self.btn_stop.setEnabled(False)
        self.btn_start.setEnabled(True)
