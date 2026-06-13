"""
2026 WC Predictor - GUI Launcher

双击此文件启动应用，无黑窗口
"""

import sys
import os
import subprocess
import threading
import webbrowser
from pathlib import Path

# 切换到脚本目录
os.chdir(Path(__file__).parent)

import tkinter as tk
from tkinter import ttk, messagebox


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("2026 WC Predictor")
        self.root.geometry("480x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")

        self.process = None
        self.running = False

        self.build_ui()

    def build_ui(self):
        # Title
        tk.Label(
            self.root, text="WC 2026 Predictor",
            font=("Arial", 22, "bold"), fg="#fbbf24", bg="#0f172a"
        ).pack(pady=(20, 5))

        tk.Label(
            self.root, text="2026 WC Prediction Tool",
            font=("Arial", 10), fg="#94a3b8", bg="#0f172a"
        ).pack(pady=(0, 15))

        # Status
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            self.root, textvariable=self.status_var,
            font=("Arial", 10), fg="#60a5fa", bg="#0f172a"
        ).pack()

        # Progress
        self.progress = ttk.Progressbar(self.root, mode="indeterminate", length=380)
        self.progress.pack(pady=10)

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#0f172a")
        btn_frame.pack(pady=10)

        self.btn_start = tk.Button(
            btn_frame, text="Start", font=("Arial", 12, "bold"),
            bg="#22c55e", fg="white", width=12, height=2,
            command=self.start, relief="flat", cursor="hand2"
        )
        self.btn_start.pack(side="left", padx=5)

        self.btn_stop = tk.Button(
            btn_frame, text="Stop", font=("Arial", 12),
            bg="#ef4444", fg="white", width=12, height=2,
            command=self.stop, relief="flat", cursor="hand2",
            state="disabled"
        )
        self.btn_stop.pack(side="left", padx=5)

        self.btn_browser = tk.Button(
            btn_frame, text="Open Browser", font=("Arial", 12),
            bg="#3b82f6", fg="white", width=12, height=2,
            command=lambda: webbrowser.open("http://localhost:8501"),
            relief="flat", cursor="hand2", state="disabled"
        )
        self.btn_browser.pack(side="left", padx=5)

        # Log
        tk.Label(
            self.root, text="Log:", font=("Arial", 9, "bold"),
            fg="#94a3b8", bg="#0f172a", anchor="w"
        ).pack(fill="x", padx=30)

        log_frame = tk.Frame(self.root, bg="#1e293b", bd=1, relief="sunken")
        log_frame.pack(padx=30, pady=(0, 15), fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame, height=10, font=("Consolas", 9),
            bg="#1e293b", fg="#e2e8f0", relief="flat",
            state="disabled", wrap="word"
        )
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True)

        # Footer
        tk.Label(
            self.root, text="URL: http://localhost:8501",
            font=("Arial", 9), fg="#475569", bg="#0f172a"
        ).pack(pady=(0, 10))

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def start(self):
        self.running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.btn_browser.config(state="normal")
        self.progress.start(15)
        self.status_var.set("Starting...")

        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            self.log("Updating data...")
            self.status_var.set("Updating data...")
            subprocess.run(
                [sys.executable, "scheduled_update.py", "--startup"],
                capture_output=True, timeout=60
            )
            self.log("Data updated")

            self.log("Starting Streamlit...")
            self.status_var.set("Running")

            self.process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "app.py",
                 "--server.port", "8501", "--server.headless", "true"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )

            for line in self.process.stdout:
                line = line.strip()
                if line:
                    self.root.after(0, self.log, line)

        except Exception as e:
            self.root.after(0, self.log, f"Error: {e}")

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            self.process = None

        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.btn_browser.config(state="disabled")
        self.progress.stop()
        self.status_var.set("Stopped")
        self.log("App stopped")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
