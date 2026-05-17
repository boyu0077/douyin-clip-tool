"""
多线程Worker封装 - 用于后台任务处理
"""
from PyQt6.QtCore import QThread, pyqtSignal


class WorkerSignals:
    """Worker信号定义（在Worker内部实例化）"""
    def __init__(self):
        self.finished = pyqtSignal(object)
        self.error = pyqtSignal(tuple)
        self.result = pyqtSignal(object)
        self.progress = pyqtSignal(int, str)


class ThreadWorker(QThread):
    """通用后台工作线程"""

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._is_cancelled = False

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.signals.finished.emit((True, result))
        except Exception as e:
            self.signals.finished.emit((False, str(e)))

    def cancel(self):
        self._is_cancelled = True
