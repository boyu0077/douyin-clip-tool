"""撤销/重做历史栈"""
from typing import Callable, Any


class UndoRedoManager:
    """撤销重做管理器"""

    def __init__(self, max_steps: int = 50):
        self._undo_stack: list[tuple[str, Callable, Callable]] = []  # (描述, undo_fn, redo_fn)
        self._redo_stack: list[tuple[str, Callable, Callable]] = []
        self._max_steps = max_steps
        self._is_undoing = False

    def execute(self, description: str, do: Callable, undo: Callable) -> Any:
        """执行操作并记录到撤销栈"""
        result = do()

        if not self._is_undoing:
            self._undo_stack.append((description, undo, do))
            self._redo_stack.clear()
            if len(self._undo_stack) > self._max_steps:
                self._undo_stack.pop(0)

        return result

    def undo(self) -> bool:
        """撤销上一步操作"""
        if not self._undo_stack:
            return False

        self._is_undoing = True
        description, undo_fn, redo_fn = self._undo_stack.pop()
        undo_fn()
        self._redo_stack.append((description, redo_fn, undo_fn))
        self._is_undoing = False
        return True

    def redo(self) -> bool:
        """重做已撤销的操作"""
        if not self._redo_stack:
            return False

        self._is_undoing = True
        description, redo_fn, undo_fn = self._redo_stack.pop()
        redo_fn()
        self._undo_stack.append((description, undo_fn, redo_fn))
        self._is_undoing = False
        return True

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def undo_description(self) -> str:
        return self._undo_stack[-1][0] if self._undo_stack else ""

    @property
    def redo_description(self) -> str:
        return self._redo_stack[-1][0] if self._redo_stack else ""

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
