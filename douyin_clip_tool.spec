# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec - 跨平台打包配置
Windows: 生成 .exe
macOS:   生成 .app
"""
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(SPECPATH)

_is_windows = sys.platform == "win32"
_is_mac = sys.platform == "darwin"

# FFmpeg二进制路径（打包时嵌入）
if _is_mac:
    FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"
    FFPROBE_BIN = "/opt/homebrew/bin/ffprobe"
else:
    FFMPEG_BIN = "ffmpeg.exe"
    FFPROBE_BIN = "ffprobe.exe"

block_cipher = None

hiddenimports = [
    "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets",
    "cv2", "numpy", "PIL", "pydub", "scipy",
    "requests", "httpx", "psutil",
]

datas = []
binaries = []

# 嵌入FFmpeg二进制（如果存在）
if os.path.exists(FFMPEG_BIN):
    binaries.append((FFMPEG_BIN, "bin"))
if os.path.exists(FFPROBE_BIN):
    binaries.append((FFPROBE_BIN, "bin"))

# 嵌入项目数据文件
for folder in ["config", "core", "ui", "editor", "processor", "dedup", "exporter", "ai_engine", "downloader", "utils"]:
    src = PROJECT_DIR / folder
    if src.exists():
        datas.append((str(src), folder))

excluded_modules = [
    "tkinter", "matplotlib", "pandas",
    "jedi", "IPython", "jupyter", "notebook",
    "faster_whisper", "ultralytics", "mediapipe",
    "librosa", "soundfile",
]

a = Analysis(
    [str(PROJECT_DIR / "main.py")],
    pathex=[str(PROJECT_DIR), str(PROJECT_DIR.parent)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="抖音切片剪辑工具",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if _is_mac:
    app = BUNDLE(
        exe,
        name="抖音切片剪辑工具.app",
        icon=None,
        bundle_identifier="com.douyin.cliptool",
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": "True",
            "CFBundleName": "抖音切片剪辑工具",
            "CFBundleDisplayName": "抖音切片剪辑工具",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
        },
    )
