"""
2026 世界杯预测工具 - 启动器

双击运行此文件即可启动应用
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import webbrowser
from pathlib import Path

class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("2026 世界杯预测工具")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # 设置图标（如果存在）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.setup_ui()
        self.process = None

    def setup_ui(self):
        """设置界面"""
        # 标题
        title_label = tk.Label(
            self.root,
            text="🏆 2026 世界杯预测工具",
            font=("Arial", 20, "bold"),
            pady=20
        )
        title_label.pack()

        # 状态标签
        self.status_label = tk.Label(
            self.root,
            text="准备启动...",
            font=("Arial", 10),
            fg="gray"
        )
        self.status_label.pack()

        # 进度条
        self.progress = ttk.Progressbar(
            self.root,
            mode='indeterminate',
            length=400
        )
        self.progress.pack(pady=20)

        # 按钮框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        # 启动按钮
        self.start_button = tk.Button(
            button_frame,
            text="🚀 启动应用",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=15,
            height=2,
            command=self.start_app
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        # 停止按钮
        self.stop_button = tk.Button(
            button_frame,
            text="⏹️ 停止应用",
            font=("Arial", 12),
            bg="#f44336",
            fg="white",
            width=15,
            height=2,
            command=self.stop_app,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # 打开浏览器按钮
        self.browser_button = tk.Button(
            button_frame,
            text="🌐 打开浏览器",
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            width=15,
            height=2,
            command=self.open_browser,
            state=tk.DISABLED
        )
        self.browser_button.pack(side=tk.LEFT, padx=10)

        # 日志文本框
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        log_label = tk.Label(log_frame, text="运行日志:", font=("Arial", 9, "bold"))
        log_label.pack(anchor=tk.W)

        self.log_text = tk.Text(
            log_frame,
            height=8,
            width=60,
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 滚动条
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

    def log(self, message):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_status(self, status):
        """更新状态"""
        self.status_label.config(text=status)

    def start_app(self):
        """启动应用"""
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.browser_button.config(state=tk.NORMAL)
        self.progress.start()

        # 在新线程中启动应用
        thread = threading.Thread(target=self.run_app, daemon=True)
        thread.start()

    def run_app(self):
        """运行应用"""
        try:
            # 更新数据
            self.update_status("正在更新数据...")
            self.log("正在更新数据...")
            self.run_command([sys.executable, "scheduled_update.py", "--startup"])

            # 启动 Streamlit
            self.update_status("正在启动应用...")
            self.log("正在启动 Streamlit 应用...")
            self.log("应用地址: http://localhost:8501")

            # 运行 Streamlit
            self.process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "app.py",
                 "--server.port", "8501", "--server.headless", "true"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # 读取输出
            for line in self.process.stdout:
                self.log(line.strip())

        except Exception as e:
            self.log(f"错误: {e}")
            self.update_status("启动失败")

    def run_command(self, command):
        """运行命令"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                self.log(f"命令执行失败: {result.stderr}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self.log("命令执行超时")
            return False
        except Exception as e:
            self.log(f"命令执行错误: {e}")
            return False

    def stop_app(self):
        """停止应用"""
        if self.process:
            self.process.terminate()
            self.process = None

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.browser_button.config(state=tk.DISABLED)
        self.progress.stop()

        self.update_status("应用已停止")
        self.log("应用已停止")

    def open_browser(self):
        """打开浏览器"""
        webbrowser.open("http://localhost:8501")

    def run(self):
        """运行启动器"""
        self.root.mainloop()

def main():
    launcher = Launcher()
    launcher.run()

if __name__ == "__main__":
    main()
