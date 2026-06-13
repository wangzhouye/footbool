@echo off
chcp 65001 >nul
title 2026 世界杯预测工具

echo ========================================
echo   2026 世界杯预测工具 - 启动脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)
echo Python 环境正常

echo.
echo [2/3] 更新数据...
python scheduled_update.py --startup
if errorlevel 1 (
    echo 警告: 数据更新失败，将使用缓存数据
)

echo.
echo [3/3] 启动应用...
echo 应用启动后，请访问: http://localhost:8501
echo.
echo 提示: 按 Ctrl+C 可以停止应用
echo ========================================

streamlit run app.py --server.port 8501 --server.headless true

pause
