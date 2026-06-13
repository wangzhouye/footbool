# 2026 世界杯预测工具 - PowerShell 启动脚本

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "2026 世界杯预测工具"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  2026 世界杯预测工具 - 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切换到脚本目录
Set-Location $PSScriptRoot

# 检查 Python
Write-Host "[1/3] 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python 版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "错误: 未找到 Python，请先安装 Python 3.11+" -ForegroundColor Red
    Read-Host "按 Enter 退出"
    exit 1
}

# 更新数据
Write-Host ""
Write-Host "[2/3] 更新数据..." -ForegroundColor Yellow
try {
    python scheduled_update.py --startup
    Write-Host "数据更新完成" -ForegroundColor Green
} catch {
    Write-Host "警告: 数据更新失败，将使用缓存数据" -ForegroundColor Yellow
}

# 启动应用
Write-Host ""
Write-Host "[3/3] 启动应用..." -ForegroundColor Yellow
Write-Host "应用启动后，请访问: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示: 按 Ctrl+C 可以停止应用" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan

streamlit run app.py --server.port 8501 --server.headless true

Read-Host "按 Enter 退出"
