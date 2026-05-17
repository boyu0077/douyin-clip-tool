#!/usr/bin/env python3
"""
抖音切片剪辑助手 - Windows桌面版
入口: python main.py
打包: pyinstaller build_exe.spec
"""
import sys
import os

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from ui.theme import apply_theme


def main():
    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("抖音切片剪辑助手")
    app.setOrganizationName("DouyinClipTool")
    
    # 应用主题
    apply_theme(app)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
