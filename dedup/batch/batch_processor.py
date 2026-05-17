"""
批量处理 - 任务队列 + 并行处理
"""
import os
import threading
import time
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class BatchTask:
    """批量任务"""
    id: str
    input_path: str
    output_path: str
    preset: str = ""
    preset_name: str = ""
    status: str = "pending"  # pending | processing | done | failed
    progress: int = 0
    error: str = ""


DedupTask = BatchTask  # 别称兼容
    

class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, max_workers: int = 3):
        self.tasks: list[BatchTask] = []
        self.max_workers = max_workers
        self._running = False
        self._executor: Optional[ThreadPoolExecutor] = None
        
        self.on_task_start: Optional[Callable] = None
        self.on_task_progress: Optional[Callable] = None
        self.on_task_done: Optional[Callable] = None
        self.on_batch_done: Optional[Callable] = None
    
    def add_task(self, input_path: str, output_path: str, preset_name: str = "Vlog去重") -> BatchTask:
        task = BatchTask(
            id=str(len(self.tasks) + 1).zfill(3),
            input_path=input_path,
            output_path=output_path,
            preset_name=preset_name,
        )
        self.tasks.append(task)
        return task
    
    def add_tasks(self, files: list[str], output_dir: str, preset_name: str = "Vlog去重"):
        """批量添加文件"""
        for i, f in enumerate(files):
            name = Path(f).stem
            out = os.path.join(output_dir, f"{name}_dedup.mp4")
            self.add_task(f, out, preset_name)
    
    def clear(self):
        self.tasks.clear()
    
    def start(self):
        """启动批量处理"""
        if self._running:
            return
        self._running = True
        
        thread = threading.Thread(target=self._process_all, daemon=True)
        thread.start()
    
    def stop(self):
        self._running = False
        from dedup.engine import dedup_engine
        dedup_engine.cancel()
    
    def _process_all(self):
        """并行处理所有任务"""
        from dedup.engine import dedup_engine
        
        pending = [t for t in self.tasks if t.status in ("pending", "failed")]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for task in pending:
                dedup_engine.cancelled = False
                future = executor.submit(
                    dedup_engine.process_video,
                    task.input_path, task.output_path, task.preset_name,
                    lambda p, msg, t=task: self._on_progress(t, p, msg)
                )
                futures[future] = task
                task.status = "processing"
                
                if self.on_task_start:
                    self.on_task_start(task)
            
            for future in as_completed(futures):
                task = futures[future]
                try:
                    success, msg = future.result()
                    task.status = "done" if success else "failed"
                    task.error = msg if not success else ""
                    task.progress = 100 if success else task.progress
                except Exception as e:
                    task.status = "failed"
                    task.error = str(e)
                
                if self.on_task_done:
                    self.on_task_done(task)
                
                if not self._running:
                    break
        
        self._running = False
        if self.on_batch_done:
            self.on_batch_done()
    
    def _on_progress(self, task: BatchTask, pct: int, msg: str):
        task.progress = pct
        if self.on_task_progress:
            self.on_task_progress(task, pct, msg)


# 全局单例
batch_processor = BatchProcessor()
