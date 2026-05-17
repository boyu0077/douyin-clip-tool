"""
CI/CD 一键构建脚本 - GitHub Actions用
将FFmpeg二进制一起打包进EXE
用法: python build_exe_ci.py
"""
import sys
import os
import shutil
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"
OUTPUT_NAME = "抖音切片剪辑工具"

# FFmpeg路径（从环境变量读取）
FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "")
FFPROBE_BIN = os.environ.get("FFPROBE_BIN", "")


def clean():
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
    spec = PROJECT_DIR / f"{OUTPUT_NAME}.spec"
    if spec.exists():
        spec.unlink()


def build():
    clean()

    # 构建add-binary参数
    add_binary = []
    if FFMPEG_BIN and os.path.exists(FFMPEG_BIN):
        add_binary += ["--add-binary", f"{FFMPEG_BIN}{os.pathsep}bin"]
        print(f"[+] 嵌入FFmpeg: {FFMPEG_BIN}")
    if FFPROBE_BIN and os.path.exists(FFPROBE_BIN):
        add_binary += ["--add-binary", f"{FFPROBE_BIN}{os.pathsep}bin"]
        print(f"[+] 嵌入FFprobe: {FFPROBE_BIN}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", OUTPUT_NAME,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "cv2",
        "--hidden-import", "numpy",
        "--hidden-import", "PIL",
        "--hidden-import", "requests",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "librosa",
        "--exclude-module", "faster_whisper",
        "--exclude-module", "ultralytics",
        "--exclude-module", "mediapipe",
    ] + add_binary + [
        str(PROJECT_DIR / "main.py"),
    ]

    print(f"\n[1/2] PyInstaller打包中...")
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR), check=False)

    if result.returncode != 0:
        print("[失败] 打包失败")
        return False

    exe_path = DIST_DIR / f"{OUTPUT_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n[2/2] 打包完成!")
        print(f"  文件: {exe_path}")
        print(f"  大小: {size_mb:.1f} MB")
        return True

    print("[失败] EXE未生成")
    return False


if __name__ == "__main__":
    print("=" * 50)
    print("  抖音切片剪辑工具 - CI EXE构建")
    print("=" * 50)
    success = build()
    if not success:
        sys.exit(1)
