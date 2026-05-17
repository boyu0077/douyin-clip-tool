"""
一键构建Windows EXE - 使用PyInstaller打包
用法: python build_exe.py
输出: dist/抖音切片剪辑工具.exe
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


def clean():
    """清理旧构建"""
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
    spec_file = PROJECT_DIR / f"{OUTPUT_NAME}.spec"
    if spec_file.exists():
        spec_file.unlink()


def build():
    """执行PyInstaller打包"""
    clean()

    # 构建PyInstaller命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", OUTPUT_NAME,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", f"config{os.pathsep}config",
        "--add-data", f"core{os.pathsep}core",
        "--add-data", f"ui{os.pathsep}ui",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "cv2",
        "--hidden-import", "numpy",
        "--hidden-import", "PIL",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "IPython",
        "--exclude-module", "jupyter",
        str(PROJECT_DIR / "main.py"),
    ]

    print(f"[1/2] 开始PyInstaller打包...")
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR), check=False)

    if result.returncode != 0:
        print("[失败] PyInstaller打包失败")
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
    print("  抖音切片剪辑工具 - Windows EXE构建")
    print("=" * 50)
    success = build()
    if not success:
        sys.exit(1)
