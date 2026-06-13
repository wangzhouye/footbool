"""
打包启动器为 exe 文件

使用方法：
    python build_exe.py
"""

import subprocess
import sys
import os

def install_pyinstaller():
    """安装 PyInstaller"""
    print("正在安装 PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_exe():
    """打包 exe"""
    print("正在打包 exe 文件...")

    # PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # 打包成单个 exe
        "--windowed",  # 不显示控制台窗口
        "--name", "世界杯预测工具",  # exe 文件名
        "--add-data", "requirements.txt;.",  # 添加依赖文件
        "--add-data", "scheduled_update.py;.",  # 添加更新脚本
        "--add-data", "app.py;.",  # 添加主应用
        "launcher.py"  # 启动器脚本
    ]

    # 执行打包
    subprocess.check_call(cmd)

    print("\n打包完成！")
    print("exe 文件位置: dist/世界杯预测工具.exe")

def main():
    # 检查是否安装了 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        install_pyinstaller()

    # 打包 exe
    build_exe()

if __name__ == "__main__":
    main()
